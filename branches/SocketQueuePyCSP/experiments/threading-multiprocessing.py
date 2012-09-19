import time
import threading
import multiprocessing

class P(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        self.X = "fisk"
        for i in range(5):
            time.sleep(1)


class T(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        self.X = "trout"
        for i in range(5):
            time.sleep(1)


p = P()
p.start()

time.sleep(1)
print p.X

t = T()
t.start()

time.sleep(1)
print t.X
t.join()

p.join()

