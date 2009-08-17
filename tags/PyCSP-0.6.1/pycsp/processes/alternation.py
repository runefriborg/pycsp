"""
Alternation module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import inspect
from channel import *

# Constants
ACTIVE, DONE, POISON, RETIRE = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

# Decorators
def choice(func):
    """
    Decorator for creating actions. It has no effect, other than improving readability
    
    >>> @choice 
    ... def action(ChannelInput):
    ...     print 'Hello'

    >>> from guard import Skip
    >>> Alternation([{Skip():action}]).execute()
    Hello
    """
    def _call(*args, **kwargs):
        return func(*args, **kwargs)
    return _call

# Classes
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
    ...     def action(ChannelInput):
    ...         L.append(ChannelInput)
    ...
    ...     alt = Alternation([{cin1:action, cin2:action}])
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
        self.guards=guards
        self.manager = ShmManager()
        pass

    def choose(self):
        req_status_id = self.manager.ReqStatusDataPool.new()
        self.manager.ReqStatus_reset(req_status_id)

        reqs={}
        try:
            pri_idx = 0
            for prioritized_item in self.guards:
                for choice in prioritized_item.keys():
                    if type(choice)==tuple: 
                        c, msg = choice
                        
                        req_id = self.manager.ChannelReqDataPool.new()
                        self.manager.ChannelReq_reset(req_id, req_status_id, msg=msg, write=True)

                        c.post_write(req_id)
                        op=WRITE
                    else:
                        c=choice

                        req_id = self.manager.ChannelReqDataPool.new()
                        self.manager.ChannelReq_reset(req_id, req_status_id)

                        c.post_read(req_id)
                        op=READ
                    reqs[choice]=(pri_idx, c, req_id, op)
                pri_idx += 1

        except (ChannelPoisonException, ChannelRetireException) as e:

            # Clean up
            self.manager.ReqStatusDataPool.retire(req_status_id)
        
            for r in reqs.keys():
                pri_idx, c, req_id, op = reqs[r]
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

        for k in reqs.keys():
            _, c, req_id, op = reqs[k]
            if op==READ:
                c.remove_read(req_id)
            else:
                c.remove_write(req_id)
            
            req = self.manager.ChannelReqDataPool.get(req_id)
            if req.result==SUCCESS:
                act=k
            elif req.result==POISON:
                poison=True
            elif req.result==RETIRE:
                retire=True

        if poison or retire:

            # Clean up
            self.manager.ReqStatusDataPool.retire(req_status_id)
            for k in reqs.keys():
                _, _, req_id, _ = reqs[k]
                self.manager.ChannelReqDataPool.retire(req_id)
            
            if poison:
                raise ChannelPoisonException()
            if retire:
                raise ChannelRetireException()

        # Read selected guard
        pri_idx, c, req_id, op = reqs[act]

        # Read msg
        req = self.manager.ChannelReqDataPool.get(req_id)
        msg = pickle.loads(self.manager.MemoryHandler.read_and_free(req.mem_id))

        # Clean up
        self.manager.ReqStatusDataPool.retire(req_status_id)
        for k in reqs.keys():
            _, _, req_id, _ = reqs[k]
            self.manager.ChannelReqDataPool.retire(req_id)

        return (pri_idx, act, c, msg, op)

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
        ...               cin1:"L1.append(ChannelInput)",
        ...               cin2:"L2.append(ChannelInput)"
        ...           }])
        ...     for i in range(n):
        ...         alt.execute()
        ...
        ...     assert((len(L1),len(L2)) == (10,5))

        >>> C1, C2 = Channel(), Channel()
        >>> Parallel(P1(OUT(C1),n=10), P1(OUT(C2),n=5), P2(IN(C1), IN(C2), n=15))
        """
        pri_idx, act, c, msg, op = self.choose()
        if self.guards[pri_idx][act]:
            action = self.guards[pri_idx][act]
            if callable(action):
                # Execute callback function
                if op==WRITE:
                    action()
                else:
                    action(ChannelInput=msg)
            else:
                # Fetch process frame and namespace
                processframe= inspect.currentframe().f_back
                
                # Compile source provided in a string.
                code = compile(action,processframe.f_code.co_filename + ' line ' + str(processframe.f_lineno) + ' in string' ,'exec')
                f_globals = processframe.f_globals
                f_locals = processframe.f_locals
                if not op==WRITE:
                    f_locals.update({'ChannelInput':msg})

                # Execute action
                exec(code, f_globals, f_locals)

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

        pri_idx, act, c, msg, op = self.choose()
        
        return (c, msg)



# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()

