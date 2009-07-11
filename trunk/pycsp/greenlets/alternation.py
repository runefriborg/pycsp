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
ACTIVE, DONE, POISON = range(3)
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
        self.s = Scheduler()

    def choose(self):
        reqs={}
        self.s.current.setstate(ACTIVE)
        try:
            pri_idx = 0
            for prioritized_item in self.guards:
                for choice in prioritized_item.keys():
                    if type(choice)==tuple: 
                        c, msg = choice                        
                        req = ChannelReq(self.s.current, msg=msg)
                        c.post_write(req)
                        op=WRITE
                    else:
                        c=choice
                        req = ChannelReq(self.s.current)
                        c.post_read(req)
                        op=READ
                    reqs[choice]=(pri_idx, c, req, op)
                pri_idx += 1

        except ChannelPoisonException:

            for r in reqs.keys():
                pri_idx, c, req, op = reqs[r]
                if op==READ:
                    c.remove_read(req)
                else:
                    c.remove_write(req)
            raise ChannelPoisonException()

        # If noone have offered a channelrequest, we wait.
        self.s.current.wait()

        act=None
        poison=False
        for k in reqs.keys():
            _, c, req, op = reqs[k]

            if req.result==SUCCESS:
                act=k
            if req.result==POISON:
                poison=True

            if op==READ:
                c.remove_read(req)
            else:
                c.remove_write(req)            

        if poison:
            raise ChannelPoisonException()

        # Read selected guard
        pri_idx, c, req, op = reqs[act]

        # Read msg
        msg = req.msg

        return (pri_idx, act, c, msg, op)

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

        pri_idx, act, c, msg, op = self.choose()
        
        return (c, msg)


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
