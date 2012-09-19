import threading
import multiprocessing
import time



def gt():
    return threading.current_thread()

def gp():
    return multiprocessing.current_process()

def sleep():
    print "sleep:"+str(gp()._parent_pid)+str(gp()._children)
    time.sleep(10)


def ct():
    t= threading.Thread(target=sleep, args=())
    t.start()
    print "ct:"+str(gp()._children)

def cp():
    p= multiprocessing.Process(target=sleep, args=())
    p.start()
    print "cp:"+str(p._parent_pid)
    

print gt()
print dir(gt())

print gp()
print dir(gp())

cp()
print gp()._parent_pid, gp()._children



ct()
