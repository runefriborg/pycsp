from common import *
from pycsp import *
from random import random

@process
def producer(jobs, bagsize, bags):
    _,outc=jobs.join(reader=False, writer=True)
    for i in range(bags):
        outc(bagsize)
    jobs.leave(reader=False, writer=True)
    
@process
def worker(jobs, results):
    inc, _=jobs.join(reader=True, writer=False)
    _,cout=results.join(reader=False, writer=True)
    try:
        while True:
            cnt=inc()
            sum = reduce(lambda x,y: x+(random()**2+random()**2<1.0), range(cnt))
            cout((cnt,sum))
    except ChannelPoisonException:
        results.leave(reader=False, writer=True)

@process
def consumer(results):
    inc, _=results.join(reader=True, writer=False)
    cnt=0
    sum=0
    try:
        while True:
            c,s=inc()
            cnt+=c
            sum+=s
    except ChannelPoisonException:
        print 4.0*sum/cnt

jobs=Channel()
results=Channel()
workers=[]

for i in range(10):
    workers.append(worker(jobs,results))
Parallel(producer(jobs,1000, 1000),
         workers,
         consumer(results))
