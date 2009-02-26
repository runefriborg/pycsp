#!/usr/bin/env python
# -*- coding: latin-1 -*-
# Copyright (c) 2007 John Markus Bjørndalen, jmb@cs.uit.no.
# See LICENSE.txt for licensing details (MIT License). 
from common import *
from pycsp import *
from pycsp.plugNplay import *

def AltTest():
    sg1 = Skip()
    sg2 = Skip()
    ch = One2OneChannel()
    alt = Alternative(sg1,sg2, ch.read)
    ret = alt.select()
    print "Returned from alt.select():", ret

def p1(cin):
    print "Bip 1"
    alt = Alternative(cin)
    for i in range(10):
        print "ding 1"
        ret = alt.select()
        print "p1: got from select:", ret, type(ret), ret()
    
def p2(cout):
    print "Bip 2"
    for i in range(10):
        cout("foo %d" % i)


def AltTest2():
    c = One2OneChannel()
    Parallel(Process(p1, c.read),
             Process(p2, c.write))

AltTest()
AltTest2()
