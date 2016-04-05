"""
Constants

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Operation type
READ, WRITE = list(range(2))

# Result of a channel request (ChannelReq)
FAIL, SUCCESS = list(range(2))

# State of a channel request status (ReqStatus)
ACTIVE, DONE = list(range(2))

# Constants used for both ChannelReq results and ReqStatus states.
POISON, RETIRE = list(range(2,4))
