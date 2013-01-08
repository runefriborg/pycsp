"""
Public and private exceptions

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Public exceptions
class ChannelPoisonException(Exception):
    """ ChannelPoisonException()

    Exception thrown by a read or write operation on a channel end.
    
    In case a ChannelPoisonException is raised in a CSP process and not caught, the CSP process
    will look for channel ends in the argument list and invoke a poison signal to every found channel end.
    
    The following network can be shutdown like this:
      >>> @process
      ... def P1(cin, cout):
      ...     while True:
      ...         cout(cin()+cin())

      >>> L1, L2, L3 = Channel(), Channel(), Channel()
      >>> Parallel(
      ...   P1(L1.reader(), L2.writer()),
      ...   P1(L2.reader(), L3.writer())       
      ... )
      >>> cout = L1.writer()

    The first P1 process will automatically propagate the signal to the other P1 process
      >>> cout.poison()

    Another configuration for process P1 using a custom propagation:
      >>> @process
      ... def P1(cin, cout):
      ...     try:
      ...         while True:
      ...             cout(cin()+cin())
      ...     except ChannelPoisonException:
      ...         print("Terminating P1")
      ...         cout.poison()
    """
    def __init__(self):
        pass

class ChannelRetireException(Exception): 
    """ ChannelRetireException()
    
    Exception thrown by a read or write operation on a channel end.

    In case a ChannelRetireException is raised in a CSP process and not caught, the CSP process
    will look for channel ends in the argument list and invoke a retire signal to every found channel end.
    
    The following network can be shutdown like this:
      >>> @process
      ... def P1(cin, cout):
      ...     while True:
      ...         cout(cin()+cin())

      >>> L1, L2, L3 = Channel(), Channel(), Channel()
      >>> Parallel(
      ...   P1(L1.reader(), L2.writer()),
      ...   P1(L2.reader(), L3.writer())       
      ... )
      >>> cout = L1.writer()

    The first P1 process will automatically propagate the signal to the other P1 process
      >>> cout.retire()

    Another configuration for process P1 using a custom propagation:
      >>> @process
      ... def P1(cin, cout):
      ...     try:
      ...         while True:
      ...             cout(cin()+cin())
      ...     except ChannelRetireException:
      ...         print("Terminating P1")
      ...         cout.retire()
    """
    def __init__(self):
        pass

class ChannelSocketException(Exception):
    """ ChannelSocketException(addr, msg)
    
    The super class for the exceptions:
      ChannelConnectException(addr, msg)
      ChannelBindException(addr, msg)
      ChannelLostException(addr, msg)
    """
    def __init__(self, addr, msg):
        self.msg = msg
        self.addr = addr
    def __str__(self):
        return repr("%s %s" % (self.msg, self.addr))

class ChannelConnectException(ChannelSocketException):
    """ ChannelConnectException(addr, msg)
    
    This exception is raised when a channel is unable to connect
    to the destination provided in the connect parameter.

    Usage:
      >>> try:
      ...     A = Channel('A', connect=('unknown', 999))
      ... except ChannelConnectException as e:
      ...     print("Addr %s is unavailable\n", % (str(e.addr)))

    If a mobile channel end is sent to another remote interpreter, where
    the channel end is unable to reconnect with the channel host, then
    a ChannelConnectException is also raised.
    """
    def __init__(self, addr, msg):
        ChannelSocketException.__init__(self, addr, msg)

class ChannelBindException(ChannelSocketException):
    """ ChannelBindException(addr, msg)
    
    This exception is raised when PyCSP is unable to bind to a port.

    The host and port to bind to is ('', 0) which binds
    to 0.0.0.0 and any available port number, unless provided through
    environment variables, configuration variables or from parameters
    to multiprocess.

    Usage:
      >>> @multiprocess(port=99)
      ... def runner(chanName):
      ...     A = Channel(chanName)
      ...     cin = A.reader()
      ...     print(cin())

      >>> try:
      ...     Parallel(runner('A'))
      ... except ChannelBindException:
      ...     print("Can not bind to port 80")
    """
    def __init__(self, addr, msg):
        ChannelSocketException.__init__(self, addr, msg)

class ChannelLostException(ChannelSocketException):
    """ ChannelLostException(addr, msg)
    
    This exception is raised when PyCSP has a channel which is left
    in an unstable state caused by a broken network connection, which
    could not be reestablished.

    Usually PyCSP can not recover from this exception.    
    """
    def __init__(self, addr, msg):
        ChannelSocketException.__init__(self, addr, msg)


class FatalException(Exception):
    """ FatalException(msg)
    
    This exception is raised if PyCSP is in an unexpected unstable state, which
    is guaranteed to be unrecoverable.
    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class InfoException(Exception):
    """ InfoException(msg)

    This exception is raised to inform that there is an error in the usage of
    PyCSP and also provide a likely solution to fix the error.
    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)
    
# Private exceptions
class AddrUnavailableException(Exception):
    def __init__(self, addr):
        self.addr = addr
    def __str__(self):
        return repr(self.addr)

class SocketException(Exception):
    def __init__(self):
        pass

class SocketDispatchException(SocketException):
    def __init__(self):
        pass
    
class SocketClosedException(SocketException):
    def __init__(self):
        pass

class SocketConnectException(SocketException):
    def __init__(self):
        pass

class SocketBindException(SocketException):
    def __init__(self, addr):
        self.addr = addr
    def __str__(self):
        return repr(self.addr)

class SocketSendException(SocketException):
    def __init__(self):
        pass
