from pycsp_import import *
from pycsp.common.trace import *

TraceInit('trace.out')

@process
def source(chan_out):
    for i in range(10):
        chan_out("Hello world (%d)\n" % (i))
    retire(chan_out)
    
@process
def sink(chan_in):
    TraceMsg('sink init')
    while True:
        sys.stdout.write(chan_in())

    TraceMsg('sink terminating')

chan = Channel()
Parallel(
    5 * source(-chan),
    5 * sink(+chan)
)

TraceQuit()
