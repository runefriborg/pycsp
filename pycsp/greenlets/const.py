"""
Constants

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""
import logging, sys
logging.basicConfig(level=logging.WARNING,
    format=' %(levelname)s:%(filename)s:%(lineno)d: %(message)s'
  )

#h1 = logging.StreamHandler(sys.stdout)
#rootLogger = logging.getLogger()
#rootLogger.addHandler(h1)

#console_logger.setFormatter(logging.Formatter(SYSLOG_FORMAT))logging.StreamHandler('/dev/stdout')

state =  {
  None: "None",
  0 : "ACTIVE",
  1 : "DONE",
  2 : "POISON",
  3 : "RETIRE",
  4 : "READ",
  5 : "WRITE",
  6 : "FAIL",
  7 : "SUCCESS"
  }
# Operation type
READ, WRITE = range(2)

# Result of a channel request (ChannelReq)
FAIL, SUCCESS = range(2)

# State of a channel request status (ReqStatus)
ACTIVE, DONE = range(2)

# Constants used for both ChannelReq results and ReqStatus states.
POISON, RETIRE = range(2,4)
