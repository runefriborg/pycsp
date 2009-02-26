#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
Contains common CSP processes such as Id, Delta, Prefix etc. 

Copyright (c) 2007 John Markus Bjørndalen, jmb@cs.uit.no.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp import process, Channel, ChannelPoisonException

@process
def Identity(cin, cout):
    """Copies its input stream to its output stream, adding a one-place buffer
    to the stream."""
    while 1:
        t = cin()
        cout(t)

@process
def Prefix(cin, cout, prefixItem=None):
    t = prefixItem
    while True:
        cout(t)
        t = cin()

@process
def Delta2(cin, cout1, cout2):
    # TODO: JCSP version sends the output in parallel. Should this be modified to do the same? 
    while True:
        t = cin()
        cout1(t)
        cout2(t)

@process
def Successor(cin, cout):
    """Adds 1 to the value read on the input channel and outputs it on the output channel.
    Infinite loop.
    """
    while True:
        cout(cin()+1)

@process
def SkipProcess():
    pass

@process
def Mux2(cin1, cin2, cout):
    alt = Alternative(cin1, cin2)
    while True:
        c = alt.priSelect()
        cout(c())
