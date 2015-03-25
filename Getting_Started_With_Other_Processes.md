# Introduction #

PyCSP provides a variety of different process types for different tasks. Table 1 shows the performance of channel communication using the [commstime](http://code.google.com/p/pycsp/source/browse/#svn/trunk/extras/examples/) benchmark for each process type on a Intel i7-2760QM CPU @ 2.40GHz running Ubuntu 12.10.

Table 1. Commstime benchmarks
| **pycsp.greenlets : @process** | ~ 0.007ms |
|:-------------------------------|:----------|
| **pycsp.parallel : @process** | ~ 0.250ms |
| **pycsp.parallel : @multiprocess** | ~ 0.415ms |

# pycsp.greenlets : @process #

The process type in pycsp.greenlets is similar to a co-routine and requires only a small overhead. It does not utilize a stack per thread, but instead handles local thread data globally in the interpreter. The greenlets is comparable to tasklets in Stackless Python, but has the benefit that they can operate in the standard CPython interpreter.

The implementation of @process in pycsp.greenlets, does not allow any communication between greenlets from different OS threads or OS processes, thus the performance is limited by the systems single-thread performance.

Up to 1.000.000 pycsp.greenlets processes has successfully been used in a single PyCSP network.

```
import pycsp.greenlets as pycsp

N = 100000

@pycsp.process
def readP(cin):
  cin()

A = pycsp.Channel("A")

pycsp.Spawn(N * readP(A.reader()))

cout = A.writer()
for i in xrange(N):
  cout(i)

pycsp.shutdown()
```


The pycsp.greenlets module translates the other process decorators, such as @multiprocess, to the standard pycsp.greenlets @process.


# pycsp.parallel / @process #

@process is implemented as an OS thread. Multiple started processes (OS threads) will be able to communicate directly without using sockets, as long as the involved channels are hosted in the same CPython Interpreter.

```
import pycsp.parallel as pycsp
from random import random

@pycsp.process
def work(cnt, result_out):
   sum = reduce(lambda x,y: x+(random()**2+random()**2<1.0), range(cnt))
   result_out((4.0*sum)/cnt)

A = pycsp.Channel("A")

pycsp.Spawn(2 * work(5000000, A.writer()))

cin = A.reader()
print("Result: %f" % ((cin()+cin())/2) )

pycsp.shutdown()
```

The GIL (CPython Global Interpreter Lock) limits the execution of parallel OS threads, when accessing Python objects. This limitation can be overcome by using @multiprocess instead.

# pycsp.parallel / @multiprocess #

This process is using the CPython multiprocessing module to run CPS processes as OS processes. All communication from a @multiprocess will be handled through sockets. Channel-ends can still be passed between/to OS processes and even between/to remote processes as the channel-ends contains the information required to reconnect the underlying sockets.

```
import pycsp.parallel as pycsp
from random import random

@pycsp.multiprocess
def work(cnt, result_out):
   sum = reduce(lambda x,y: x+(random()**2+random()**2<1.0), range(cnt))
   result_out((4.0*sum)/cnt)

A = pycsp.Channel("A")

pycsp.Spawn(2 * work(5000000, A.writer()))

cin = A.reader()
print("Result: %f" % ((cin()+cin())/2) )

pycsp.shutdown()
```

See [Remote connections](Getting_Started_With_Parallel.md) for more information on how to connect remote processes using PyCSP channels.