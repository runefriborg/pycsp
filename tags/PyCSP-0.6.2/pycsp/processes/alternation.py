"""
Alternation module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import inspect
import types
from channel import *

# Constants
ACTIVE, DONE, POISON, RETIRE = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

# Decorators
def choice(func):
    """
    Decorator for creating choice objets
    
    >>> @choice
    ... def action(__channel_input=None):
    ...     print 'Hello'

    >>> from guard import Skip
    >>> Alternation([{Skip():action()}]).execute()
    Hello
    """
    # __choice_fn func_name used to identify function in Alternation.execute
    def __choice_fn(*args, **kwargs):
        return Choice(func, *args, **kwargs)
    return __choice_fn

# Classes
class Choice:
    """ Choice(func, *args, **kwargs)
    It is recommended to use the @choice decorator, to create Choice instances
    """
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def invoke_on_input(self, __channel_input):
        self.kwargs['__channel_input'] = __channel_input
        self.fn(*self.args, **self.kwargs)
        del self.kwargs['__channel_input']

    def invoke_on_output(self):
        self.fn(*self.args, **self.kwargs)


class Alternation:
    """
    Alternation supports input and output guards. Guards are ChannelEnd
    or Guard objects.
    
    Note that alternation always performs the guard that was chosen,
    i.e. channel input or output is executed within the alternation so
    even the empty choice with an alternation execution or a choice where
    the results are simply ignored, still performs the guarded input or
    output.

    >>> from __init__ import *

    >>> @process
    ... def P1(cout, n=5):
    ...     for i in range(n):
    ...         cout(i)
    
    >>> @process
    ... def P2(cin1, cin2, n=10):
    ...     L = []
    ...
    ...     @choice
    ...     def action(__channel_input):
    ...         L.append(__channel_input)
    ...
    ...     alt = Alternation([{cin1:action(), cin2:action()}])
    ...     for i in range(n):
    ...         alt.execute()
    ...
    ...     assert(len(L) == 10)
    ...     L.sort()
    ...     assert(L == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4])
                
    >>> C1, C2 = Channel(), Channel()
    >>> Parallel(P1(OUT(C1)), P1(OUT(C2)), P2(IN(C1), IN(C2)))
    
    """

    def __init__(self, guards):
        # Preserve tuple entries and convert dictionary entries to tuple entries
        self.guards = []
        for g in guards:
            if type(g) == types.TupleType:
                self.guards.append(g)
            elif type(g) == types.DictType:
                for elem in g.keys():
                    if type(elem) == types.TupleType:
                        self.guards.append((elem[0], elem[1], g[elem]))
                    else:
                        self.guards.append((elem, g[elem]))

        # The internal representation of guards is a prioritized list
        # of tuples:
        #   input guard: (channel end, action) 
        #   output guard: (channel end, msg, action)

        self.manager = ShmManager()

    def choose(self):
        req_status_id = self.manager.ReqStatusDataPool.new()
        self.manager.ReqStatus_reset(req_status_id)

        reqs={}
        try:
            idx = 0
            for prio_item in self.guards:
                if len(prio_item) == 3:
                    c, msg, action = prio_item

                    req_id = self.manager.ChannelReqDataPool.new()
                    self.manager.ChannelReq_reset(req_id, req_status_id, msg=msg, write=True)

                    c.post_write(req_id)
                    op=WRITE
                else:
                    c, action = prio_item

                    req_id = self.manager.ChannelReqDataPool.new()
                    self.manager.ChannelReq_reset(req_id, req_status_id)

                    c.post_read(req_id)
                    op=READ
                reqs[req_id]=(idx, c, op)
                idx += 1

        except (ChannelPoisonException, ChannelRetireException) as e:

            # Clean up
            self.manager.ReqStatusDataPool.retire(req_status_id)

            for req_id in reqs.keys():
                _, c, op = reqs[req_id]
                if op==READ:
                    c.remove_read(req_id)
                else:
                    c.remove_write(req_id)
                self.manager.ChannelReqDataPool.retire(req_id)

            raise e

        # If noone have offered a channelrequest, we wait.
        self.manager.ReqStatus_wait(req_status_id)

        act=None
        poison=False
        retire=False

        for req_id in reqs.keys():
            _, c, op = reqs[req_id]
            if op==READ:
                c.remove_read(req_id)
            else:
                c.remove_write(req_id)
            
            req = self.manager.ChannelReqDataPool.get(req_id)
            if req.result==SUCCESS:
                act=req_id
            elif req.result==POISON:
                poison=True
            elif req.result==RETIRE:
                retire=True

        if poison or retire:

            # Clean up
            self.manager.ReqStatusDataPool.retire(req_status_id)
            for req_id in reqs.keys():
                self.manager.ChannelReqDataPool.retire(req_id)
            
            if poison:
                raise ChannelPoisonException()
            if retire:
                raise ChannelRetireException()

        # Read selected guard
        idx, c, op = reqs[act]

        # Read msg
        req = self.manager.ChannelReqDataPool.get(act)
        msg = pickle.loads(self.manager.MemoryHandler.read_and_free(req.mem_id))

        # Clean up
        self.manager.ReqStatusDataPool.retire(req_status_id)
        for req_id in reqs.keys():
            self.manager.ChannelReqDataPool.retire(req_id)

        return (idx, c, msg, op)

    def execute(self):
        """
        Selects the guard and executes the attached action. Action is a function or python code passed in a string.

        >>> from __init__ import *

        >>> @process
        ... def P1(cout, n):
        ...     for i in range(n):
        ...         cout(i)

        >>> @process
        ... def P2(cin1, cin2, n):
        ...     L1,L2 = [],[]
        ...     alt = Alternation([{
        ...               cin1:"L1.append(__channel_input)",
        ...               cin2:"L2.append(__channel_input)"
        ...           }])
        ...     for i in range(n):
        ...         alt.execute()
        ...
        ...     assert((len(L1),len(L2)) == (10,5))

        >>> C1, C2 = Channel(), Channel()
        >>> Parallel(P1(OUT(C1),n=10), P1(OUT(C2),n=5), P2(IN(C1), IN(C2), n=15))
        """
        idx, c, msg, op = self.choose()
        if self.guards[idx]:
            action = self.guards[idx][-1]

            # Executing Choice object method
            if isinstance(action, Choice):
                if op==WRITE:
                    action.invoke_on_output()
                else:
                    action.invoke_on_input(msg)

            # Executing callback function object
            elif callable(action):
                # Choice function not allowed as callback
                if type(action) == types.FunctionType and action.func_name == '__choice_fn':
                    raise Exception('@choice function is not instantiated. Please use action() and not just action')
                else:
                    # Execute callback function
                    if op==WRITE:
                        action()
                    else:
                        action(__channel_input=msg)

            # Compiling and executing string
            elif type(action) == types.StringType:
                # Fetch process frame and namespace
                processframe= inspect.currentframe().f_back
                
                # Compile source provided in a string.
                code = compile(action,processframe.f_code.co_filename + ' line ' + str(processframe.f_lineno) + ' in string' ,'exec')
                f_globals = processframe.f_globals
                f_locals = processframe.f_locals
                if op==READ:
                    f_locals.update({'__channel_input':msg})

                # Execute action
                exec(code, f_globals, f_locals)

            elif type(action) == types.NoneType:
                pass
            else:
                raise Exception('Failed executing action: '+str(action))

    def select(self):
        """
        Selects the guard.

        >>> from __init__ import *

        >>> @process
        ... def P1(cout, n=5):
        ...     for i in range(n):
        ...         cout(i)

        >>> @process
        ... def P2(cin1, cin2, n=10):
        ...     L1,L2 = [],[]
        ...     alt = Alternation([{
        ...               cin1:None,
        ...               cin2:None
        ...           }])
        ...     for i in range(n):
        ...         (g, msg) = alt.select()
        ...         if g == cin1:
        ...             L1.append(msg)
        ...         if g == cin2:
        ...             L2.append(msg)
        ...
        ...     assert((len(L1),len(L2)) == (5,5))

        >>> C1, C2 = Channel(), Channel()
        >>> Parallel(P1(OUT(C1)), P1(OUT(C2)), P2(IN(C1), IN(C2)))
        """
        idx, c, msg, op = self.choose()        
        return (c, msg)



# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()

