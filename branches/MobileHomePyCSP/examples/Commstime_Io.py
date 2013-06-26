"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *
import time

@process
def Prefix(cin, cout, prefixItem=None):
    t = prefixItem
    while True:
        cout(t)
        t = empty(cin())

@process
def Delta2(cin, cout1, cout2):
    while True:
        t = empty(cin())
        cout1(t)
        cout2(t)


@process
def Successor(cin, cout):
    """Adds 1 to the value read on the input channel and outputs it on the output channel.
    Infinite loop.
    """
    while True:
        cout(empty(cin()+1))

@io
def empty(i):
    return i

@process
def Consumer(cin):
    "Commstime consumer process"
    N = 1000
    ts = time.time
    t1 = ts()
    cin()
    t1 = ts()
    for i in range(N):
        empty(cin())
    t2 = ts()
    dt = t2-t1
    tchan = dt / (4 * N)
    print "DT = %f.\nTime per ch : %f/(4*%d) = %f s = %f us" % \
        (dt, dt, N, tchan, tchan * 1000000)
    print "consumer done, posioning channel"
    retire(cin)

@process
def CommsTimeBM():
    # Create channels
    a = Channel("a")
    b = Channel("b")
    c = Channel("c")
    d = Channel("d")

    print "Running commstime test"
    Parallel(Prefix(c.reader(), a.writer(), prefixItem = 0),  # initiator
             Delta2(a.reader(), b.writer(), d.writer()),         # forwarding to two
             Successor(b.reader(), c.writer()),               # feeding back to prefix
             Consumer(d.reader()))                         # timing process

N_BM = 10
for i in range(N_BM):
    print "----------- run %d/%d -------------" % (i+1, N_BM)
    Parallel(CommsTimeBM())


shutdown()
