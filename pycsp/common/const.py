"""
Constants

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""
import os

ENVVAL_PROCTYPE = 'PYCSP_MULTIPROCESSING'
ENVVAL_PORT = 'PYCSP_PORT'


# Setup
PICKLE_PROTOCOL= 0
CONNECT_TIMEOUT = 10
CONNECT_RETRY_DELAY = 0.1

BIND_TIMEOUT = 10
BIND_RETRY_DELAY = 1

# Operation type
READ, WRITE = range(2)

# Constants used for both ChannelReq results and ReqStatus states.
READY, FAIL, SUCCESS, POISON, RETIRE = range(5)

