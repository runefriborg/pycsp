
import threading
import time

N = 1000
K = 1000

def get(l):
    #return l.pop(0)
    while (not l):
        time.sleep(0.001)
    return l.pop(0)

def put(l, item):
    #l.append(item)
    l.append(item)

def init(buf):
    #return []
    return []

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
