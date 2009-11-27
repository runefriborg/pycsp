"""
Configuration module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Constants
NET_SERVER_ID = 0

# Classes
class Configuration(object):
    """
    Configuration is a singleton class.
    
    >>> A = Configuration()
    >>> B = Configuration()
    >>> A == B
    True

    Retrieve value
    >>> Configuration().get(NET_SERVER_ID)
    42

    Set value
    >>> Configuration().set(NET_SERVER_ID, 25)
    >>> Configuration().get(NET_SERVER_ID)
    25
    """

    __instance = None  # the unique instance
    __conf = {}

    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self):
        pass
    
    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:
            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)
            
            cls.__conf = {
                NET_SERVER_ID:42
                }
            
        return cls.__instance
    getInstance = classmethod(getInstance)

    def get(self, conf_id):
        return self.__conf[conf_id]

    def set(self, conf_id, value):
        self.__conf[conf_id] = value

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
