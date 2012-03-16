import threading
import time
import atexit


shutdown = False

    
@atexit.register
def goodbye():
    import threading
    if threading.currentThread().name == "MainThread":
        for x in globals().values():
            if isinstance(x, Test):
                x.close()
        print "del"
    else:
        print "pis!"

def fiskT():
    global shutdown
    print "running fisk"
    while not shutdown:
        print "R",
        time.sleep(1)
    print "Nice shutdown"

class Test(object):
    def __init__(self):
        
        thread = threading.Thread(target=fiskT)
        thread.daemon=True
        thread.start()
        self.thread = thread
        print "init"

    def close(self):
        global shutdown
        shutdown = True
        print "close"
        self.thread.join()

t = Test()

