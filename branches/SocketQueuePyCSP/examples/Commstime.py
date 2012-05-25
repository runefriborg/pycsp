#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *
import time

@process
def Prefix(cin, cout, prefixItem=None):
    print 'Started Prefix'
    t = prefixItem
    while True:
        cout(t)
        t = cin()

@process
def Delta2(cin, cout1, cout2):
    print 'Started Delta2'
    while True:
        t = cin()
        cout1(t)
        cout2(t)

@process
def Successor(cin, cout):
    """Adds 1 to the value read on the input channel and outputs it on the output channel.
    Infinite loop.
    """
    print 'Started Successor'
    while True:
        cout(cin()+1)

@process
def Consumer(cin):
    "Commstime consumer process"
    print 'Started Consumer'
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
    poison(cin)

def CommsTimeBM():
    # Create channels
    a = Channel("a")
    b = Channel("b")
    c = Channel("c")
    d = Channel("d")

    print a.address
    print b.address

    print "Running commstime test"
    Parallel(Prefix(+c, -a, prefixItem = 0),  # initiator
             Delta2(+a, -b, -d),         # forwarding to two
             Successor(+b, -c),               # feeding back to prefix
             Consumer(+d))                         # timing process
    print "commstime test done"


N_BM = 1
for i in range(N_BM):
    print "----------- run %d/%d -------------" % (i+1, N_BM)
    CommsTimeBM()

print "The end"
