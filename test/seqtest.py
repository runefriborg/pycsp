#!/usr/bin/env python
# -*- coding: latin-1 -*-
# Copyright (c) 2007 John Markus Bjørndalen, jmb@cs.uit.no.
# See LICENSE.txt for licensing details (MIT License).

from common import *
from pycsp import *
from pycsp.plugNplay import *

def TestProc(n):
    print "This is test proc", n

Sequence(Process(TestProc, 1),
         Process(TestProc, 2),
         Process(TestProc, 3))




@process
def TestProc2(n):
    print "This is test proc", n

Sequence(TestProc2(1),
         TestProc2(2),
         TestProc2(3))
