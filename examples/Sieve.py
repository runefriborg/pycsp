"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *

@process
def producer(cout, cnt):
    for i in range(2,cnt):
        cout(i)
    poison(cout)
    
@process
def worker(cin, cout):
    try:
        ccout=None
        my_prime=cin()
        cout(my_prime)
        child_channel=Channel()
        ccout=child_channel.writer()
        Spawn(worker(child_channel.reader(), cout))
        while True:
            new_prime=cin()
            if new_prime%my_prime:
                ccout(new_prime)
    except ChannelPoisonException:
        if ccout:
            poison(ccout)
        else:
            poison(cout)

@process
def printer(cin):
    while True:
        print cin()


first=Channel()
outc=Channel()

Parallel(producer(first.writer(),2000),
         worker(first.reader(), outc.writer()),
         printer(outc.reader()))


shutdown()
