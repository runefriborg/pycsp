
import threading
import time

N = 1000
K = 1000

class OwnQueue():
    def __init__(self):
        self.lock = threading.Condition()
        self.items = []
        self.waiting = False

    def pop(self):
        
        # Pre test
        if self.items:
            return self.items.pop(0)

        self.lock.acquire()
        if not self.items:
            self.waiting = True
            self.lock.wait()
        obj = self.items.pop(0)
        self.waiting = False
        self.lock.release()

        return obj

    def push(self, obj):
        self.lock.acquire()
        self.items.append(obj)
        if self.waiting:
            self.lock.notify()
        self.lock.release()

def get(l):
    #return l.pop(0)
    return l.pop()

def put(l, item):
    #l.append(item)
    l.push(item)

def init(buf):
    #return []
    return OwnQueue()

def writeThread(qlist):
    for i in xrange(N):
        for k in xrange(K):
            m = get(qlist[i])
        #print "GOT %s" % (m)

qlist = []
for i in xrange(N):
    qlist.append(init(100))

t = threading.Thread(target=writeThread, args=(qlist,))
t.start()    

for i in xrange(N):
    for k in xrange(K):
        put(qlist[i], k)

t.join()
