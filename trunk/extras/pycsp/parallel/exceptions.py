"""
Public and private exceptions

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Public exceptions
class ChannelPoisonException(Exception):
    def __init__(self):
        pass

class ChannelRetireException(Exception): 
    def __init__(self):
        pass

class ChannelSocketException(Exception):
    def __init__(self, addr, msg):
        self.msg = msg
        self.addr = addr
    def __str__(self):
        return repr("%s %s" % (self.msg, self.addr))

class ChannelConnectException(ChannelSocketException):
    def __init__(self, addr, msg):
        ChannelSocketException.__init__(self, addr, msg)

class ChannelBindException(ChannelSocketException):
    def __init__(self, addr, msg):
        ChannelSocketException.__init__(self, addr, msg)

class ChannelLostException(ChannelSocketException):
    def __init__(self, addr, msg):
        ChannelSocketException.__init__(self, addr, msg)


class FatalException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class InfoException(Exception):
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
