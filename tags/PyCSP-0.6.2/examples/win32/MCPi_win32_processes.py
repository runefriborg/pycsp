from common import *
from random import random
import sys

def producer(job_out, bagsize, bags):
    for i in range(bags):
        job_out(bagsize)
    retire(job_out)
    
def worker(job_in, result_out):
    while True:
        cnt=job_in()
        sum = reduce(lambda x,y: x+(random()**2+random()**2<1.0), range(cnt))
        result_out((cnt,sum))

def consumer(result_in):
    cnt=0
    sum=0
    try:
        while True:
            c,s=result_in()
            cnt+=c
            sum+=s
    except ChannelRetireException:
        print 4.0*sum/cnt

if __name__ == '__main__':
    jobs=Channel()
    results=Channel()
    workers=[]

    for i in range(4):
        workers.append(Process(worker, IN(jobs),OUT(results)))
    Parallel(Process(producer, OUT(jobs),10000, 1000),
             workers,
             Process(consumer,IN(results)))
