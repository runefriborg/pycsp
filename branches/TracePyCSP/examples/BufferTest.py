from pycsp_import import *
from pycsp.common.trace import *

TraceInit()

A = Channel('fisk', buffer=10)

print A

@process
def P1(cout):
    for i in range(100):
        cout(i)
    retire(cout)
    cout('fisk')

@process
def P2(cin):
    while True:
        print cin()

Parallel(P1(A.writer()), P2(A.reader()))



TraceQuit()
