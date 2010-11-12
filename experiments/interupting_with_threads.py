import greenlet
import time
import threading
# Global val
value = [0]


import threading

def tcode(val):
    for i in range(1000):
        value[0] = 0
        time.sleep(0.001)
        print val

for a in range(10):
    t = threading.Thread(target=tcode, args=('Yo',))
    t.start()



def update(friend, quit):
    while True:
        value[0] += 1
        print value,
        friend.switch(greenlet.getcurrent(), quit)
        if value[0] > 1000:
            quit.switch()


g1,g2 = greenlet.greenlet(update), greenlet.greenlet(update)
g1.switch(g2, greenlet.getcurrent())

