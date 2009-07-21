from common import *
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
Parallel([source(OUT(chan)) for i in range(5)],
          [sink(IN(chan))    for i in range(5)])
