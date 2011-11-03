"""
Constants

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""
import os
ENVVAL_DEBUG = "PYCSP_DEBUG"

# Operation type
READ, WRITE = range(2)

# Constants used for both ChannelReq results and ReqStatus states.
READY, FAIL, SUCCESS, POISON, RETIRE = range(5)

# Exceptions
class ChannelPoisonException(Exception): 
    def __init__(self):
        pass

class ChannelRetireException(Exception): 
    def __init__(self):
        pass


class SocketClosedException(Exception):
    def __init__(self):
        pass
