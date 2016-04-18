"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *
from pycsp.common.plugNplay import *

# We are using plugNplay processes
#  Prefix
#  Pairs
#  Delta2

@process
def Printer(cin, limit):
    for i in range(limit):
        print(cin())
    poison(cin)

A = Channel('A')
B = Channel('B')
C = Channel('C')
D = Channel('D')
printC = Channel()

Parallel(
    Prefix(+B, -A, prefix=0),
    Prefix(+C, -B, prefix=1),
    Pairs(+D, -C),
    Delta2(+A, -D, -printC),
    Printer(+printC, limit=20)
)

shutdown()
