#!/usr/bin/env python
# -*- coding: latin-1 -*-
from common import *
from pycsp import *
from pycsp.plugNplay import *
import os

@process
def Consumer(cin):
    "Commstime consumer process"
    N = 5000
    ts = time.time
    t1 = ts()
    cin()
    t1 = ts()
    for i in range(N):
        cin()
    t2 = ts()
    dt = t2-t1
    tchan = dt / (4 * N)
    print "DT = %f.\nTime per ch : %f/(4*%d) = %f s = %f us" % \
          (dt, dt, N, tchan, tchan * 1000000)
    print "consumer done, posioning channel"
    poisonChannel(cin)

def CommsTimeBM():
    # Create channels
    a = One2OneChannel("a")
    b = One2OneChannel("b")
    c = One2OneChannel("c")
    d = One2OneChannel("d")

    print "Running commstime test"
    # Rather than pass the objects and get the channel ends wrong, or doing complex
    # addons like in csp.net, i simply pass the write and read functions as channel ends.
    # Note: c.read.im_self == c, also check im_func, im_class
    Parallel(Prefix(c.read, a.write, prefixItem = 0),  # initiator
             Delta2(a.read, b.write, d.write),         # forwarding to two
             Successor(b.read, c.write),               # feeding back to prefix
             Consumer(d.read))                         # timing process

N_BM = 10
for i in range(N_BM):
    print "----------- run %d/%d -------------" % (i+1, N_BM)
    CommsTimeBM()

# A bit of a hack, but windows does not have uname()
try:
    os.uname()
except:
    print "Sleeping for a while to allow windows users to read benchmark results"
    time.sleep(15)
