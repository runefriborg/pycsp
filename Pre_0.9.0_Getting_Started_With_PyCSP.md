# Introduction #

PyCSP provides an API that can be used to write concurrent
applications using [CSP (Communicating Sequential Processes)](http://en.wikipedia.org/wiki/Communicating_sequential_processes).

The API is implemented in four versions:
Threads, processes, greenlets and net. All implementations share an
almost identical API making it trivial to switch from one implementation to
another.

  * pycsp.threads - A CSP process is implemented as an OS thread. The internal synchronization is handled by thread-locking mechanisms. This is the default implementation. Because of the Python Global Interpeter Lock, this is best suited for applications that spend most of their time in external routines.

  * pycsp.processes - A CSP process is implemented as an OS process. The internal synchronization is more complex than pycsp.threads and is built on top of the multiprocessing module available in Python 2.6. This implementation is not affected by the Global Interpreter Lock, but has some limitations on a Windows OS and generally has a larger communication overhead than the threaded version.

  * pycsp.greenlets - This uses co-routines instead of threads. Greenlets is a simple co-routine implementation and can be downloaded [here](http://pypi.python.org/pypi/greenlet). It provides the possibility to create 100.000 CSP processes in a single CSP network. This version is optimal for single-core architectures since it provides the fastest communication.

  * pycsp.net - A proof-of-concept net implementation of pycsp.threads. All synchronization is handled in a single process. This provides the same functionality as pycsp.threads, but adding a larger cost and a bottleneck by introducing the ChannelServerProcess. It requires Pyro (http://pyro.sourceforge.net/) for communication.


Requirements:
  * pycsp.threads - Works with the entire Python 2.x string.
  * pycsp.processes - Needs the [multiprocessing](http://docs.python.org/library/multiprocessing.html) module available in Python 2.6+
  * pycsp.greenlets - Requires the [greenlet](http://pypi.python.org/pypi/greenlet) module
  * pycsp.net - Requires [Pyro](http://www.xs4all.nl/~irmen/pyro3/) 3.8+

# Contents #



# Installing #

Start by fetching the latest [tarball](http://code.google.com/p/pycsp/downloads/list).

Unpack and to install run

```
python setup.py install
```

You can now try starting your python interpreter and type `import pycsp`. If no errors, then you are good to go. The default implementation is always pycsp.threads.

```
>>> import pycsp
>>> print pycsp.version
(0, 7, 1, 'threads')
```

# Elements of PyCSP #

Open a new file and put

```
from pycsp.threads import *
```

as your first line.

## Processes ##

This is a process with one output channel end:

```
@process
def counter(cout, limit=1000)
  for i in xrange(limit):
    cout(i)
```


To start two instances of our newly created counter process we have the following options.

### In parallel ###

The Parallel construct will block until both counter processes have terminated.

```
Parallel(counter(...), counter(...))
```

They can also be started asynchronously by using the Spawn construct.

```
Spawn(counter(...), counter(...))
```

### In sequence ###

The Sequence construct will block until both counter processes have terminated. Only one process will be execute at any possible time and will be executed in the order they are provided.

```
Sequence(counter(...), counter(...))
```







## Channels and channel ends ##

Channels can have any number of readers and writers and will block until a read or write have been committed to the opposite action.

```
A = Channel('A')
```

To communicate on a channel you are required to join it first.

`cin = A.reader()` or `cout = A.writer()`


# A Simple Application #

```
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
```

Output:
```
0 1 2 3 4 5 6 7 8 9
```


# More Examples #

For a lot more [examples](http://code.google.com/p/pycsp/source/browse/#svn/trunk/examples).