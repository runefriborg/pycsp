"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
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
   10 * worker( jobs.reader() ,results.writer()),
   consumer(results.reader()))
