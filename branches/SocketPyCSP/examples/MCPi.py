"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *
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
           print str(cnt) + ' ' + str(sum)
           sum=(sum*cnt+result_in())/(cnt+1)    #Get result
   except ChannelRetireException:
       print 'Result:',sum            #We are done - print result

jobs=Channel()
results=Channel()


Parallel(
   producer( jobs.writer() , 10000, 1000),
   4 * worker( jobs.reader() ,results.writer()),
   consumer(results.reader()))
