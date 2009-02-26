#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
Measuring one-way and two-way (two channels) latency for PyCSP over network channels. 
"""
from common import *
from pycsp import *
from pycsp.plugNplay import *
from pycsp.net import *
import time
import sys

N_WARM = 10
N_ROUNDS = 10
N_ITERS = 1000

@process
def server():
    print "# Server"
    c1 = One2OneChannel()
    c2 = One2OneChannel()
    registerNamedChannel(c1, "to-serv")
    registerNamedChannel(c2, "from-serv")
    # phase 1: send one way (client->master)
    for i in range(N_WARM):
        c1.read()
    for n in range(N_ROUNDS):
        for i in range(N_ITERS):
            c1.read()
    # phase 2: send both ways (client->master, master->client)
    for i in range(N_WARM):
        c1.read()
        c2.write(42)
    for n in range(N_ROUNDS):
        for i in range(N_ITERS):
            c1.read()
            c2.write(42)

@process
def client():
    print "# Client"
    c1 = getNamedChannel("to-serv")
    c2 = getNamedChannel("from-serv")
    # phase 1: send one way (client->master)
    print "results_oneway = ["
    for i in range(N_WARM):
        c1.write(42)
    for n in range(N_ROUNDS):
        t0 = time.time()
        for i in range(N_ITERS):
            c1.write(42)
        t1 = time.time()
        dtr = 1000000.0 * (t1-t0) / N_ITERS
        print "%f, # microseconds per send" % (dtr, )
    # phase 2: send both ways (client->master, master->client)
    print "]"
    print "results_twoway = ["
    for i in range(N_WARM):
        c1.write(42)
        c2.read()
    for n in range(N_ROUNDS):
        t0 = time.time()
        for i in range(N_ITERS):
            c1.write(42)
            c2.read()
        t1 = time.time()
        dtr = 1000000.0 * (t1-t0) / N_ITERS
        print "%f, # microseconds per send" % (dtr, )
    print "]"
        

if sys.argv[1].lower() == "-s":
    print "starting server"
    Sequence(server())
elif sys.argv[1].lower() == "-c":
    Sequence(client())
else:
    print "Usage: ", sys.argv[0], " [-s/-c], where -s means server end and -c means client end"
    print "The client side prints benchmark output"
    
