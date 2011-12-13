

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
