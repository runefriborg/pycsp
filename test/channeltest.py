#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
Copyright (c) 2007 John Markus Bjørndalen, jmb@cs.uit.no.
See LICENSE.txt for licensing details (MIT License).
"""
from common import *
from pycsp import *
from pycsp.plugNplay import *
import threading
import time

N = 5


def WN(cout):
    pid = threading.currentThread()
    for i in range(N):
        print "  [%s] Writing %d" % (pid, i)
        cout(i)
        time.sleep(0.1)
    print "Writer [%s] wrote all" % pid
    poisonChannel(cout)

def RN(cin):
    pid = threading.currentThread()
    for i in range(N):
        v = cin()
        print "  [%s] Reading %d" % (pid, v)
        time.sleep(0.1)
    print "Reader [%s] got all" % pid
    poisonChannel(cin)

# TODO: Robert
def FastWN(cout):
    pid = threading.currentThread()
    for i in range(50):
        print "  [%s] Writing %d" % (pid, i)
        cout(i)
        #time.sleep(0.1)
    print "Writer [%s] wrote all" % pid
    poisonChannel(cout)

# TODO: Robert
def FastRN(cin):
    pid = threading.currentThread()
    try:
        while 1:
            v = cin()
            print "  [%s] Reading %d" % (pid, v)
    except ChannelPoisonException:
        print 'Reader [%s] caught poison exception' % pid

def o2otest():
    print "-----------------------"
    print "Testing One2One Channel"
    print "Reader and writer should both report as done"
    c = One2OneChannel()
    Parallel(Process(WN, c.write),
             Process(RN, c.read))

def o2atest():
    print "-----------------------"
    print "Testing One2Any Channel"
    print "Writer should report as done, none of the readers should"
    c = One2AnyChannel()
    Parallel(Process(WN, c.write),
             Process(RN, c.read),
             Process(RN, c.read))
    
def a2otest():
    print "-----------------------"
    print "Testing Any2One Channel"
    print "Reader should report as done, none of the writers should"
    c = Any2OneChannel()
    Parallel(Process(WN, c.write),
             Process(WN, c.write),
             Process(RN, c.read))

def a2atest():
    print "-----------------------"
    print "Testing Any2Any Channel"
    print "All readers and writers should report as done"
    # TODO: potential race if one of the writers/readers finish early and poison the channel!
    # the same problem might occur above as well! 
    c = Any2AnyChannel()
    Parallel(Process(WN, c.write),
             Process(WN, c.write),
             Process(RN, c.read),
             Process(RN, c.read))


def bo2otest():
    print "-----------------------"
    print "Testing BufferedOne2One Channel"
    print "Reader and writer should both report as done"
    c = BufferedOne2OneChannel()
    Parallel(Process(FastWN, c.write),
             Process(FastRN, c.read))


o2otest()
o2atest()
a2otest()
a2atest()
bo2otest()
