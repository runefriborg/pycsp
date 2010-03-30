"""
Alternation module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
  
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Imports
import inspect
import types
from channel import ChannelPoisonException, ChannelRetireException, ChannelReq 
from scheduling import Scheduler
from const import *

# Decorators
def choice(func):
    """
    Decorator for creating choice objets
    
    >>> from __init__ import *
    >>> @choice
    ... def action(channel_input=None):
    ...     print 'Hello'

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

    def invoke_on_input(self, channel_input):
        self.kwargs['channel_input'] = channel_input
        self.fn(*self.args, **self.kwargs)
        del self.kwargs['channel_input']

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

    >>> L = []

    >>> @choice 
    ... def action(channel_input):
    ...     L.append(channel_input)

    >>> @process
    ... def P1(cout, n=5):
    ...     for i in range(n):
    ...         cout(i)
    
    >>> @process
    ... def P2(cin1, cin2, n=10):
    ...     alt = Alternation([{cin1:action(), cin2:action()}])
    ...     for i in range(n):
    ...         alt.execute()
                
    >>> C1, C2 = Channel(), Channel()
    >>> Parallel(P1(OUT(C1)), P1(OUT(C2)), P2(IN(C1), IN(C2)))

    >>> len(L)
    10

    >>> L.sort()
    >>> L
    [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
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

        self.s = Scheduler()

        # Default is to go one up in stackframe.
        self.execute_frame = -1

    def set_execute_frame(self, steps):
        if steps > 0:
            self.execute_frame = -1*steps
        else:
            self.execute_frame = steps

    def choose(self):
        #logging.warning("deadline choose, guards: %s"%self.guards)

        reqs={}
        self.s.current.setstate(ACTIVE)
        try:
            idx = 0
            for prio_item in self.guards:
                #logging.warning("%s,%s,%s"%prio_item)
                if len(prio_item) == 3:
                    c, msg, action = prio_item
                    req = ChannelReq(self.s.current, msg=msg)
                    c.post_write(req)
                    op=WRITE
                else:
                    c, action = prio_item
                    req = ChannelReq(self.s.current)
                    c.post_read(req)
                    op=READ
                reqs[req]=(idx, c, op)
                idx += 1
            logging.debug("reqs: %s"%reqs) 
        except (ChannelPoisonException, ChannelRetireException) as e:
            for req in reqs.keys():
                _, c, op = reqs[req]
                if op==READ:
                    c.remove_read(req)
                else:
                    c.remove_write(req)
            raise e
            
        # If noone have offered a channelrequest, we wait.
        self.s.current.wait()
        act=None
        poison=False
        retire=False
        logging.warning("Returned self:%s"%self.s.current)
        logging.warning("reqs2: %s"%reqs) 
        for req in reqs.keys():
            _, c, op = reqs[req]
            if op==READ:
                c.remove_read(req)
            else:
                c.remove_write(req)            

            if req.result==SUCCESS:
                act=req

            if req.result==POISON:
                poison=True
            if req.result==RETIRE:
                retire=True

        if not act:
            if poison:
                raise ChannelPoisonException()
            if retire:
                raise ChannelRetireException()

        idx, c, op = reqs[act]
        logging.debug("\n\tidx:%s,\n\tc: %s,\n\top: %s"%(idx,c,op))

        return (idx, act, c, op)


#        idx, req, c, op = self.choose()
#        return (c, req.msg)

    def execute(self):
        """
        Selects the guard and executes the attached action. Action is a function or python code passed in a string.

        >>> from __init__ import *
        >>> L1,L2 = [],[]

        >>> @process
        ... def P1(cout, n):
        ...     for i in range(n):
        ...         cout(i)

        >>> @process
        ... def P2(cin1, cin2, n):
        ...     alt = Alternation([{
        ...               cin1:"L1.append(channel_input)",
        ...               cin2:"L2.append(channel_input)"
        ...           }])
        ...     for i in range(n):
        ...         alt.execute()

        >>> C1, C2 = Channel(), Channel()
        >>> Parallel(P1(OUT(C1),n=10), P1(OUT(C2),n=5), P2(IN(C1), IN(C2), n=15))

        >>> len(L1), len(L2)
        (10, 5)
        """
        idx, req, c, op = self.choose()
        if self.guards[idx]:
            action = self.guards[idx][-1]

            # Executing Choice object method
            if isinstance(action, Choice):
                if op==WRITE:
                    action.invoke_on_output()
                else:
                    action.invoke_on_input(req.msg)

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
                        action(channel_input=req.msg)

            # Compiling and executing string
            elif type(action) == types.StringType:
                # Fetch process frame and namespace
                processframe= inspect.currentframe()
                steps = self.execute_frame
                #logging.warning("steps:%s"%steps)
                while (steps < 0):
                    #code = compile(action,processframe.f_code.co_filename + ' line ' + str(processframe.f_lineno) + ' in string' ,'exec')
                    #logging.warning("%s : %s"%(processframe,code))
                    processframe = processframe.f_back
                    steps += 1
                #logging.warning(processframe)
                # Compile source provided in a string.
                code = compile(action,processframe.f_code.co_filename + ' line ' + str(processframe.f_lineno) + ' in string' ,'exec')
                f_globals = processframe.f_globals
                f_locals = processframe.f_locals
                #logging.warning("alternation:\n\tcode %s"%(code))
                
                if op==READ:
                    f_locals.update({'channel_input':req.msg})
                # Execute action
                exec(code, f_globals, f_locals)

            elif type(action) == types.NoneType:
                pass
            else:
                raise Exception('Failed executing action: '+str(action))

        return (c, req.msg)

    def select(self):
        """
        Selects the guard.

        >>> from __init__ import *
        >>> L1,L2 = [],[]

        >>> @process
        ... def P1(cout, n=5):
        ...     for i in range(n):
        ...         cout(i)

        >>> @process
        ... def P2(cin1, cin2, n=10):
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

        >>> C1, C2 = Channel(), Channel()
        >>> Parallel(P1(OUT(C1)), P1(OUT(C2)), P2(IN(C1), IN(C2)))

        >>> len(L1), len(L2)
        (5, 5)
        """
        idx, req, c, op = self.choose()
        return (c, req.msg)


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
