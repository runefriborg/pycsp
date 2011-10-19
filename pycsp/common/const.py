"""
Constants

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

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



