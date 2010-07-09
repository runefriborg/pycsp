#!/usr/bin/env python
# -*- coding: latin-1 -*-
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
import time
import math
import numpy

k=10
D=72
N=400

@process
def find_kNN(body_in, body_out, result_out, local, k):
    best = []
    body_out(local)
    local_id, local_params = local
    while True:
        body_id, body_params = body_in()
        if body_id == local_id:
            result_out((local_id,best))
            return # done
        else:            
            dist = numpy.sum((body_params-local_params)**2)
            dist = math.sqrt(dist)
            best.append((dist,body_id))

            # Sorts on first element.
            best.sort()
            if (len(best) > k):
                best.pop()

            body_out((body_id, body_params))

        
def setup_random(dims, dlen):
    keys=numpy.array([i for i in xrange(dlen)])
    values=numpy.zeros(dlen)
    data=numpy.random.rand(dlen, dims)
    return keys,values,data


keys, values, targets = setup_random(D, N)
print "targets has",len(targets[0]),"dimensions and",len(targets),"entries."

# Start time
t1=time.time()

resultChan = Channel()

# Create process chain
chan = Channel(buffer=1)
first = chan.writer()
chain = chan.writer()
prev = chan
for i in xrange(N-1):
    chan = Channel()
    Spawn(find_kNN(prev.reader(), chan.writer(), resultChan.writer(), (i,targets[i]), k))
    prev = chan
Spawn(find_kNN(prev.reader(), first, resultChan.writer(), (N-1,targets[N-1]), k))

get = resultChan.reader()
win = []
for i in xrange(N):
    win.append(get())

# Shutdown chain.
poison(chain)

# Compute time
t2=time.time()
print "Found in", t2-t1



