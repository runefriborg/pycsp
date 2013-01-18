"""
PlugNPlay module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""
import pycsp.current

@pycsp.current.process
def Identity(cin, cout):
    """Copies its input stream to its output stream, adding a one-place buffer
    to the stream."""
    while True:
        t = cin()
        cout(t)

@pycsp.current.process
def Prefix(cin, cout, prefix=None):
    t = prefix
    while True:
        cout(t)
        t = cin()

@pycsp.current.process
def Successor(cin, cout):
    """Adds 1 to the value read on the input channel and outputs it on the output channel.
    Infinite loop.
    """
    while True:
        cout(cin()+1)

@pycsp.current.process
def Delta2(cin, cout1, cout2):
    while True:
        msg = cin()
        pycsp.current.Alternation([{
            (cout1,msg):'cout2(msg)',
            (cout2,msg):'cout1(msg)'
            }]).execute()

@pycsp.current.process
def Plus(cin1, cin2, cout):
    while True:
        cout(cin1() + cin2())

@pycsp.current.process
def Tail(cin, cout):
    dispose = cin()
    while True:
        cout(cin())

@pycsp.current.process
def Pairs(cin, cout):
    pA, pB, pC = pycsp.current.Channel('pA'), pycsp.current.Channel('pB'), pycsp.current.Channel('pC')
    pycsp.current.Parallel(
        Delta2(cin, -pA, -pB),
        Plus(+pA, +pC, cout),
        Tail(+pB, -pC)
    )

@pycsp.current.process
def SkipProcess():
    pass

@pycsp.current.process
def Mux2(cin1, cin2, cout):
    alt = pycsp.current.Alternation([{cin1:None, cin2:None}])
    while True:
        guard, msg = alt.select()
        cout(msg)
