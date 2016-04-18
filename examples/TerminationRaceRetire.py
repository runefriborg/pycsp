"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *
import sys

@process
def source(chan_out):
    for i in range(10):
        chan_out("Hello world (%d)\n" % (i))
    retire(chan_out)
    
@process
def sink(chan_in):
    while True:
        sys.stdout.write(chan_in())

chan = Channel()
Parallel(source(chan.writer()) * 5,
         sink(chan.reader())   * 5)

shutdown()
