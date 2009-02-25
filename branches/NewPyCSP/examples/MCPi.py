from common import *
from pycsp import *
from random import random
import sys

@process
def producer(job_out, bagsize, bags):
    for i in range(bags):
        job_out(bagsize)
    retire(job_out)
    
@process
def worker(job_in, result_out):
    while True:
        cnt=job_in()
        sum = reduce(lambda x,y: x+(random()**2+random()**2<1.0), range(cnt))
        result_out((cnt,sum))

@process
def consumer(result_in):
    cnt=0
    sum=0
    try:
        while True:
            c,s=result_in()
            cnt+=c
            sum+=s
    except ChannelPoisonException:
        print 4.0*sum/cnt

jobs=Channel()
results=Channel()
workers=[]

for i in range(10):
    workers.append(worker(IN(jobs),OUT(results)))
Parallel(producer(OUT(jobs),1000, 1000),
         workers,
         consumer(IN(results)))
