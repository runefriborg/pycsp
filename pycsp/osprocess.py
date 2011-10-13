
import os

ENVVAL = 'PYCSP_MULTIPROCESSING'

if os.environ.has_key(ENVVAL) and not os.environ[ENVVAL] == '':
    from multiprocessing import Process as Proc    

    def getProcName():
        p = osprocess.current_process()
        name = p.name
        if name == 'MainProcess':
            return '__mainproc__'
        else:
            return name
        
else:
    from threading import Thread as Proc

    def getProcName():
        try:
            # compatible with Python 2.6+
            t = osprocess.current_thread()
            name = t.name
        except AttributeError:
            # compatible with Python 2.5- 
            t = threading.currentThread()
            name = t.getName()
    
        if name == 'MainThread':
            return '__mainproc__'
        else:
            return name





