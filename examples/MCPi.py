from common import *
from random import random

@process
def producer(job_out, bagsize, bags):
   for i in range(bags): job_out(bagsize)
   retire(job_out)

@process
def worker(job_in, result_out):
   while True:
       cnt=job_in()           #Get task
       sum = reduce(lambda x,y: x+(random()**2+random()**2<1.0), range(cnt))
       
       result_out((4.0*sum)/cnt)  #Forward result

@process
def consumer(result_in):
   cnt=0; sum=result_in()    #Get first result
   try:
       while True:
           cnt+=1
           print sum
           sum=(sum*cnt+result_in())/(cnt+1)    #Get result
   except ChannelRetireException:
       print 'Result:',sum            #We are done - print result

jobs=Channel()
results=Channel()

Parallel(producer(OUT(jobs),1000, 10000),
        [worker(IN(jobs),OUT(results)) for i in range(10)],
        consumer(IN(results)))
