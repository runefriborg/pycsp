# Exceptions
class ChannelPoisonException(Exception): 
    def __init__(self):
        pass

class ChannelRetireException(Exception): 
    def __init__(self):
        pass

class SocketException(Exception):
    def __init__(self):
        pass
    
class SocketClosedException(SocketException):
    def __init__(self):
        pass

class SocketConnectException(SocketException):
    def __init__(self):
        pass

class SocketBindException(SocketException):
    def __init__(self):
        pass
