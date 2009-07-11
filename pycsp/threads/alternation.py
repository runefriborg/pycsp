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

    >>> L = []

    >>> @choice 
    ... def action(ChannelInput):
    ...     L.append(ChannelInput)

    >>> @process
    ... def P1(cout, n=5):
    ...     for i in range(n):
    ...         cout(i)
    
    >>> @process
    ... def P2(cin1, cin2, n=10):
    ...     alt = Alternation([{cin1:action, cin2:action}])
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
        self.guards=guards
        pass

    def choose(self):
        req_status=ReqStatus()
        reqs={}
        try:
            pri_idx = 0
            for prioritized_item in self.guards:
                for choice in prioritized_item.keys():
                    if type(choice)==tuple: 
                        c, msg = choice
                        req=ChannelReq(req_status,msg=msg)
                        c.post_write(req)
                        op=WRITE
                    else:
                        req=ChannelReq(req_status)
                        c=choice
                        c.post_read(req)
                        op=READ
                    reqs[choice]=(pri_idx, c, req, op)
                pri_idx += 1
        except (ChannelPoisonException, ChannelRetireException) as e:
            for r in reqs.keys():
                pri_idx, c, req, op = reqs[r]
                if op==READ:
                    c.remove_read(req)
                else:
                    c.remove_write(req)
            raise e
        req_status.cond.acquire()
        if req.status.state==ACTIVE:
            req_status.cond.wait()
        req_status.cond.release()
        act=None
        poison=False
        retire=False
        for k in reqs.keys():
            pri_idx, c, req, op = reqs[k]
            if op==READ:
                c.remove_read(req)
            else:
                c.remove_write(req)
            if req.result==SUCCESS:
                act=k
            if req.result==POISON:
                poison=True
            if req.result==RETIRE:
                retire=True
        if poison:
            raise ChannelPoisonException()
        if retire:
            raise ChannelRetireException()

        pri_idx, c, req, op = reqs[act]

        return (pri_idx, act, c, req, op)

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
        ...               cin1:"L1.append(ChannelInput)",
        ...               cin2:"L2.append(ChannelInput)"
        ...           }])
        ...     for i in range(n):
        ...         alt.execute()

        >>> C1, C2 = Channel(), Channel()
        >>> Parallel(P1(OUT(C1),n=10), P1(OUT(C2),n=5), P2(IN(C1), IN(C2), n=15))

        >>> len(L1), len(L2)
        (10, 5)
        """
        pri_idx, act, c, req, op = self.choose()
        if self.guards[pri_idx][act]:
            action = self.guards[pri_idx][act]
            if callable(action):
                # Execute callback function
                if op==WRITE:
                    action()
                else:
                    action(ChannelInput=req.msg)
            else:
                # Fetch process frame and namespace
                processframe= inspect.currentframe().f_back
                
                # Compile source provided in a string.
                code = compile(action,processframe.f_code.co_filename + ' line ' + str(processframe.f_lineno) + ' in string' ,'exec')
                f_globals = processframe.f_globals
                f_locals = processframe.f_locals
                if not op==WRITE:
                    f_locals.update({'ChannelInput':req.msg})

                # Execute action
                exec(code, f_globals, f_locals)

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

        pri_idx, act, c, req, op = self.choose()
        return (c, req.msg)



# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
