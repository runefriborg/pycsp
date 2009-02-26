#!/usr/bin/env python
# -*- coding: latin-1 -*-
# Copyright (c) 2007 John Markus Bjørndalen, jmb@cs.uit.no.
# See LICENSE.txt for licensing details (MIT License).

from common import *
from pycsp import *
from pycsp.plugNplay import *

@process
def PoisonTest(cout):
    for i in range(100):
        print i
        cout(i)
    poisonChannel(cout)

def test():
    a = One2OneChannel("a")
    b = One2OneChannel("b")
    c = One2OneChannel("c")
    d = BlackHoleChannel("d")

    Parallel(PoisonTest(a.write),
             Identity(a.read, b.write),
             Identity(b.read, c.write),
             Identity(c.read, d.write))
    for ch in [a,b,c,d]:
        print "State of channel", ch.name, "- poisoned is", ch.poisoned

@process
def PoisonReader(cin):
    for i in range(100):
        r = cin()
        print i, r
    cin.poison()

@process
def Count(cout):
    i = 0
    while 1:
        cout(i)
        i += 1

def test2():
    a = Any2OneChannel()
    Parallel(Count(a.write),
             Count(a.write),
             PoisonReader(a.read))
    print "Processes done"

if __name__ == "__main__":
    test()
    test2()
