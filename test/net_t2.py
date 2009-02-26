#!/usr/bin/env python
# -*- coding: latin-1 -*-
from common import *
from pycsp import *
from pycsp.plugNplay import *
from pycsp.net import *

@process
def test1():
    print "Test1"
    waitForSignal()
    c = getNamedChannel("foo1")
    print "- Trying to write to channel"
    print "-", c.write("I'm here")
    print "- Trying next write (should be poisoned)"
    c.write("I'm here")
    print "---poison failed   !!!!!"

@process
def test2():
    print "Test2"
    waitForSignal()
    c = getNamedChannel("foo2")
    print "- Trying to write to channel"
    c.write("I'm here")
    time.sleep(2)
    print "- poisoning channel method"
    time.sleep(1)
    poisonChannel(c.read)
        
@process
def test3():
    print "Test3"
    waitForSignal()
    ca = getNamedChannel("foo3a")
    cb = getNamedChannel("foo3b")
    print "- Trying to write to channel"
    ca.write("I'm here")
    print "- Trying to use Alt on channel b"
    alt = Alternative(cb.read)
    ret = alt.select()
    print "-  returned from alt.select():", ret
    print "-  reading                   :", ret()
    print "- Done"


def waitForSignal():
    "Waits until the other side has registered its channels"
    global ctrl
    ctrl.read()

ctrl = getNamedChannel("foo")
Sequence(test1())
Sequence(test2())
Sequence(test3())
ctrl.read()
print "all tests done"
time.sleep(1)
