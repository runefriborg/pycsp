"""
Constants

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""
import threading
ENVVAL_PORT = 'PYCSP_PORT'

# Setup
PICKLE_PROTOCOL= 0

# Operation type
READ, WRITE = range(2)

# Constants used for both ChannelReq results and ReqStatus states.
READY, FAIL, SUCCESS, POISON, RETIRE = range(5)


def getThreadAndName():
    import multiprocessing
    mname = multiprocessing.current_process().name
    try:
        # compatible with Python 2.6+
        t = threading.current_thread()
        name = mname + t.name
    except AttributeError:
        # compatible with Python 2.5- 
        t = threading.currentThread()
        name = mname + t.getName()

    if name == 'MainThread':
        try:
            if t.id:
                name = t.id
        except AttributeError:
            print "atterror"
            pass
            
    return (t, name)
