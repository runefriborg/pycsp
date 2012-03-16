
import Queue
import threading

def get(l):
    #return l.pop(0)
    return l.get()

def put(l, item):
    #l.append(item)
    l.put(item)

def init(n):
    #return []
    return Queue.Queue(100)

def writeThread(qlist):
    for i in xrange(10000):
        m = get(qlist[i])
        #print "GOT %s" % (m)

qlist = []
for i in xrange(10000):
    qlist.append(init(100))

t = threading.Thread(target=writeThread, args=(qlist,))
t.start()    

for i in xrange(10000):
    put(qlist[i], i)

t.join()
