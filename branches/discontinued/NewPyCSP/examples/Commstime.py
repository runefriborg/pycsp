#!/usr/bin/env python
# -*- coding: latin-1 -*-
from common import *
from pycsp import *
import time

@process
def Prefix(cin, cout, prefixItem=None):
    t = prefixItem
    while True:
        cout(t)
        t = cin()

@process
def Delta2(cin, cout1, cout2):
    while True:
        t = cin()
        cout1(t)
        cout2(t)


@process
def Successor(cin, cout):
    """Adds 1 to the value read on the input channel and outputs it on the output channel.
    Infinite loop.
    """
    while True:
        cout(cin()+1)

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
    retire(cin)

def CommsTimeBM():
    # Create channels
    a = Channel("a")
    b = Channel("b")
    c = Channel("c")
    d = Channel("d")

    print "Running commstime test"
    Parallel(Prefix(IN(c), OUT(a), prefixItem = 0),  # initiator
             Delta2(IN(a), OUT(b), OUT(d)),         # forwarding to two
             Successor(IN(b), OUT(c)),               # feeding back to prefix
             Consumer(IN(d)))                         # timing process

N_BM = 10
for i in range(N_BM):
    print "----------- run %d/%d -------------" % (i+1, N_BM)
    CommsTimeBM()

