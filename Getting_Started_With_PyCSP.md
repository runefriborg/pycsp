# Introduction #

PyCSP provides an API that can be used to write concurrent
applications using [CSP (Communicating Sequential Processes)](http://en.wikipedia.org/wiki/Communicating_sequential_processes).

The API is implemented in two versions:
One implementation any mix of communication between threads, multiprocesses and distributed processes. The other provides a light-weight thread approach for running everything in a single thread. Both implementations share an almost identical API making it trivial to switch from one implementation to another.

  * pycsp.parallel - A CSP process network may consists of OS threads and OS processes spread across a network, or it may just be OS threads running in a single OS process. The internal synchronization is handled by a mix of thread-locking mechanism and socket communication. This implementation is the most flexible and provides the means for running CSP networks on clusters or just for dynamic network communication.

  * pycsp.greenlets - This uses co-routines instead of OS threads/processes. Greenlets is a simple co-routine implementation and can be downloaded [here](http://pypi.python.org/pypi/greenlet). It provides the possibility to create 100.000 CSP processes in a single CSP network on a single host. This version is optimal for single-core architectures since it provides the fastest communication.

Requirements:
  * pycsp.parallel - Works with the entire Python 2.x string, but needs the multiprocessing module for supporting OS processes ([multiprocessing](http://docs.python.org/library/multiprocessing.html) module available in Python 2.6+).
  * pycsp.greenlets - Requires the [greenlet](http://pypi.python.org/pypi/greenlet) module

# Contents #



# Installing #

```
wget http://pycsp.googlecode.com/files/pycsp-complete-0.9.0.tar.gz
tar -zxf pycsp-complete-0.9.0.tar.gz
cd pycsp-0.9.0
sudo python setup.py install
```

You can now try starting your python interpreter and type `import pycsp.parallel`. If no errors, then you are good to go.

```
>>> import pycsp.parallel as pycsp
>>> print pycsp.version
(0, 9, 0, 'parallel')
>>> pycsp.shutdown()
>>> quit
```

# Elements of PyCSP #

Open a new file and put

```
import pycsp.parallel as pycsp
```

as your first line.

## Processes ##

This is a process with one output channel end:

```
@pycsp.process
def counter(cout, limit=1000)
  for i in xrange(limit):
    cout(i)
```


To start two instances of our newly created counter process we have the following options.

### In parallel ###

The Parallel construct will block until both counter processes have terminated.

```
pycsp.Parallel(counter(...), counter(...))
```

They can also be started asynchronously by using the Spawn construct.

```
pycsp.Spawn(counter(...), counter(...))
```

### In sequence ###

The Sequence construct will block until both counter processes have terminated. Only one process will be execute at any possible time and will be executed in the order they are provided.

```
pycsp.Sequence(counter(...), counter(...))
```







## Channels and channel ends ##

Channels can have any number of readers and writers and will block until a read or write have been committed to the opposite action.

```
A = pycsp.Channel('A')
```

To communicate on a channel you are required to join it first.

`cin = A.reader()` or `cout = A.writer()`

## Closing the PYCSP instance ##

Every PyCSP application will create a server thread, to serve incoming communications on channels. For this reason, it is required that you always end your PyCSP application with a call to shutdown()

```
pycsp.shutdown()
```

# A Simple Application #

```
from pycsp.parallel import *

@process
def counter(cout, limit):
  for i in xrange(limit):
    cout(i)
  poison(cout)

@process
def printer(cin):
  while True:
    print cin(),

A = Channel('A')
Parallel(
  counter(A.writer(), limit=10),
  printer(A.reader())
)

shutdown()
```

Output:
```
0 1 2 3 4 5 6 7 8 9
```


# More Examples #

For a lot more [examples](http://code.google.com/p/pycsp/source/browse/#svn/trunk/base/examples).