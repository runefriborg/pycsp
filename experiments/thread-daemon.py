import threading
import time

class T(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        sT = subT()
        sT.start()
        print "Running"

        print "Quitting"

class subT(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
        self.daemon = True

    def run(self):
        while (True):
            print "subT alive!"
            time.sleep(1)


t = T()
t.start()
t.join()


print "Has subT quit?  Waiting 10 seconds"
time.sleep(10)
