from pycsp_import import *


@process
def source1(chan_out):
    for i in range(10):
        chan_out("Hello world (%d)\n" % (i))

@process
def source2(chan_out):
    for i in range(10):
        chan_out("Hello world (%d)\n" % (i))
    retire(chan_out)
   
@process
def sink(chan_in):
    while True:
        sys.stdout.write(chan_in())

chan = Channel()
Spawn(sink(+chan))

print chan.sync

Parallel( source1(-chan) )

print chan.sync

Parallel(source2(-chan)*2)

print chan.sync




