"""
Constructs added to allow easy switching between PyCSP implementations.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

class Io(object):
    pass

def io(func):
    """
    @io decorator for blocking io operations.
    In PyCSP threading it has no effect, other than compatibility

    >>> @io
    ... def sleep(n):
    ...     import time
    ...     time.sleep(n)

    >>> sleep(0.01)
    """
    return func
