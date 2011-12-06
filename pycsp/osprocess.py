
import os
import threading
from pycsp.common.const import *


def getThreadAndName():
    try:
        # compatible with Python 2.6+
        t = threading.current_thread()
        name = t.name
    except AttributeError:
        # compatible with Python 2.5- 
        t = threading.currentThread()
        name = t.getName()
    return (t, name)

if os.environ.has_key(ENVVAL_PROCTYPE) and not os.environ[ENVVAL_PROCTYPE] == '':
    import multiprocessing
    from multiprocessing import Process as Proc

    def getProc():
        return multiprocessing.current_process()

    def getProcName():
        p = getProc()
        name = p.name
        if name == 'MainProcess':
            return '__mainproc__'
        else:
            return name
        
else:
    from threading import Thread as Proc

    def getProc():
        t, _ = getThreadAndName()
        return t

    def getProcName():
        _, name = getThreadAndName()    
        if name == 'MainThread':
            return '__mainproc__'
        else:
            return name





