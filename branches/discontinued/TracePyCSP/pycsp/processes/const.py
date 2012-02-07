"""
Constants

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Operation type
READ, WRITE = range(2)

# Result of a channel request (ChannelReq)
FAIL, SUCCESS = range(2)

# State of a channel request status (ReqStatus)
ACTIVE, DONE = range(2)

# Constants used for both ChannelReq results and ReqStatus states.
POISON, RETIRE = range(2,4)
