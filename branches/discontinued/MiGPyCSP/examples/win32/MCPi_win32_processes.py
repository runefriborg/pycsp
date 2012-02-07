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
        workers.append(Process(worker, jobs.reader(), results.writer()))
    Parallel(Process(producer, jobs.writer(),10000, 1000),
             workers,
             Process(consumer, results.reader()))
