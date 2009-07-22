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

    >>> from __init__ import *    
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
class RealAlternation:
    """
    RealAlternation is the Alternation object that handles synchronization
    at the channel server daemon.
    """

    def __init__(self, guards):
        self.guards=guards

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
            elif req.result==POISON:
                poison=True
            elif req.result==RETIRE:
                retire=True
        if poison:
            raise ChannelPoisonException()
        if retire:
            raise ChannelRetireException()
        pri_idx, c, req, op = reqs[act]
        return (pri_idx, act, c, req, op)




# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
