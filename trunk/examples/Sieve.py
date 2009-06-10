from common import *

@process
def producer(cout, cnt):
    for i in range(2,cnt):
        cout(i)
    poison(cout)
    
@process
def worker(cin, cout):
    try:
        ccout=None
        my_prime=cin()
        cout(my_prime)
        child_channel=Channel()
        ccout=OUT(child_channel)
        Spawn(worker(IN(child_channel), cout))
        while True:
            new_prime=cin()
            if new_prime%my_prime:
                ccout(new_prime)
    except ChannelPoisonException:
        if ccout:
            poison(ccout)
        else:
            poison(cout)

@process
def printer(cin):
    while True:
        print cin()


first=Channel()
outc=Channel()

Parallel(producer(OUT(first),2000),
         worker(IN(first), OUT(outc)),
         printer(IN(outc)))
