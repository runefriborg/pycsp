import logging, sys
logging.basicConfig(level=logging.WARNING,
    format=' %(levelname)s:%(filename)s:%(lineno)d: %(message)s'
  )

#h1 = logging.StreamHandler(sys.stdout)
#rootLogger = logging.getLogger()
#rootLogger.addHandler(h1)

#console_logger.setFormatter(logging.Formatter(SYSLOG_FORMAT))logging.StreamHandler('/dev/stdout')
# Constants
ACTIVE, DONE, POISON, RETIRE, READ, WRITE, FAIL, SUCCESS = range(8)

state =  {
  0 : "ACTIVE",
  1 : "DONE",
  2 : "POISON",
  3 : "RETIRE",
  4 : "READ",
  5 : "WRITE",
  6 : "FAIL",
  7 : "SUCCESS"
  }
