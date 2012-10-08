

import threading
import multiprocessing
import time

Fisk = threading.local()

def task(name):
    Fisk.__dict__["VAL1"] = name
    time.sleep(5)
    print Fisk.VAL1

t = threading.Thread(target=task, args=('Therese',))
t.start()

t2 = threading.Thread(target=task, args=('Bjoern',))
t2.start()

t.join()
t2.join()

print "DONE"
print Fisk.VAL1
