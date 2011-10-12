
import os

ENVVAL = 'PYCSP_MULTIPROCESSING'

if not os.environ.has_key(ENVVAL):
    from threading import Thread as Proc
else:
    if os.environ[ENVVAL] == '':
        from threading import Thread as Proc
    else:
        from multiprocessing import Process as Proc




