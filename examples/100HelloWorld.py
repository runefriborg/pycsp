from pycsp_import import *
from pycsp.net import *
from pycsp.common.grid import *

@grid_process(vgrid='DIKU')
def source(chan_out):
    for i in range(10):
        chan_out("HelloWorld (%d)\n" % (i))
    retire(chan_out)

GridInit()
server.start(host=public_ip)

chan = Channel()
Spawn(100 * source(-chan))

# Read
cin = +chan
try:
    while True:
        cin()
except ChannelRetireException:
    print 'Received 1000 HelloWorld.'
