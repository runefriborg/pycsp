#!/usr/bin/env python
# -*- coding: latin-1 -*-
from common import *
from pycsp import *
from pycsp.plugNplay import *
from pycsp.net import *
import time


@process
def test1():
    print "Test1"
    c = One2OneChannel()
    registerNamedChannel(c, "foo1")
    signalReady()
    print "- Trying to read from channel"
    print "-", c.read()
    time.sleep(1)
    print "- poisoning channel"
    poisonChannel(c.read)  # this works, as well as poisoning the channel itself. 
    print "- done"

@process
def test2(): 
    print "Test2"
    c = One2OneChannel()
    registerNamedChannel(c, "foo2")
    signalReady()
    print "- Trying to read from channel"
    print "-", c.read()
    print "- Another read (should be poisoned)"
    r = c.read()
    print "-", r
    print "---poison failed !!!!"

@process
def test3():
    print "Test3 - tests an input guard across the network"
    ca = One2OneChannel()
    cb = One2OneChannel()
    registerNamedChannel(ca, "foo3a")
    registerNamedChannel(cb, "foo3b")
    signalReady()
    print "- Trying to read from channel"
    print "- ", ca.read()
    print "- waiting 3 seconds before writing to channel b"
    time.sleep(3)
    cb.write("here you go")
    
    
def signalReady():
    "signals that this end has registered the necessary channels for this test"
    global ctrl
    ctrl.write("ready") 

ctrl = One2OneChannel()
registerNamedChannel(ctrl, "foo")
Sequence(test1())
Sequence(test2())
Sequence(test3())
ctrl.write("done")
print "all tests done"
time.sleep(1)
