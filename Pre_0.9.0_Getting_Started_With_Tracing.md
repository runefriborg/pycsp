# Introduction #

All PyCSP executions can be traced using the pycsp.common.trace module. It must be imported into the current pycsp namespace after a previous import of a pycsp implementation. Like this:

```
from pycsp.processes import *
from pycsp.common.trace import *
```

or

```
import pycsp.processes as csp
import pycsp.common.trace as csp
```


This wraps the standard PyCSP API into a trace enabled API, which will communicate with a single process writing the trace log. Before calling the PyCSP API, the trace process must be started using

```
TraceInit(<filename>, stdout=<True | False>)
```

and then eventually, when the PyCSP processes have terminated TraceQuit() must be called to end the trace process.

```
TraceQuit()
```

A process may also update the trace file with messages using TraceMsg()

```
TraceMsg(< str >)
```


The written trace file is updated with every new trace update, thus it can be piped and read interactively. If no filename is provided to TraceInit(), the default filename is pycsp\_trace.log.

# Example #

```
from pycsp.threads import *
from pycsp.common.trace import *

TraceInit()

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

TraceQuit()
```

writes the following trace file:

```
$ cat pycsp_trace.log 
{'chan_name': 'A', 'type': 'Channel'}
{'chan_name': 'A', 'type': 'ChannelEndWrite'}
{'chan_name': 'A', 'type': 'ChannelEndRead'}
{'processes': [{'func_name': 'counter', 'process_id': '0.4117670563381288341841.38'}, {'func_name': 'printer', 'process_id': '0.5632834914361288341841.38'}], 'process_id': '__main__', 'type': 'BlockOnParallel'}
{'func_name': 'counter', 'process_id': '0.4117670563381288341841.38', 'type': 'StartProcess'}
{'func_name': 'printer', 'process_id': '0.5632834914361288341841.38', 'type': 'StartProcess'}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'BlockOnWrite', 'id': 0}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 0}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'DoneRead', 'id': 0}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'DoneWrite', 'id': 0}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 1}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'BlockOnWrite', 'id': 1}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'DoneWrite', 'id': 1}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'DoneRead', 'id': 1}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'BlockOnWrite', 'id': 2}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 2}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'DoneRead', 'id': 2}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 3}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'DoneWrite', 'id': 2}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'BlockOnWrite', 'id': 3}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'DoneRead', 'id': 3}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'DoneWrite', 'id': 3}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 4}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'BlockOnWrite', 'id': 4}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'DoneWrite', 'id': 4}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'DoneRead', 'id': 4}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'BlockOnWrite', 'id': 5}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 5}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'DoneRead', 'id': 5}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'DoneWrite', 'id': 5}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 6}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'BlockOnWrite', 'id': 6}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'DoneWrite', 'id': 6}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'DoneRead', 'id': 6}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'BlockOnWrite', 'id': 7}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 7}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'DoneWrite', 'id': 7}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'BlockOnWrite', 'id': 8}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'DoneRead', 'id': 7}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 8}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'DoneRead', 'id': 8}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'DoneWrite', 'id': 8}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 9}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'BlockOnWrite', 'id': 9}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'DoneWrite', 'id': 9}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'DoneRead', 'id': 9}
{'process_id': '0.4117670563381288341841.38', 'chan_name': 'A', 'type': 'Poison', 'id': 10}
{'func_name': 'counter', 'process_id': '0.4117670563381288341841.38', 'type': 'QuitProcess'}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'BlockOnRead', 'id': 10}
{'func_name': 'printer', 'process_id': '0.5632834914361288341841.38', 'type': 'QuitProcess'}
{'process_id': '0.5632834914361288341841.38', 'chan_name': 'A', 'type': 'Poison', 'id': 10}
{'processes': [{'func_name': 'counter', 'process_id': '0.4117670563381288341841.38'}, {'func_name': 'printer', 'process_id': '0.5632834914361288341841.38'}], 'process_id': '__main__', 'type': 'DoneParallel'}
{'type': 'TraceQuit'}
```

# Using PlayTrace.py #

In the tools folder of the PyCSP download you will find the PlayTrace.py tool. Executing this

```
$ python PlayTrace.py

Play a trace of a PyCSP application

Usage:
  python PlayTrace.py <trace file>

Requires:
  Graphviz
  wxPython 2.8+
  PyCSP
```

Then running PlayTrace.py with produced pycsp\_trace.log

```
$ python tools/PlayTrace.py pycsp_trace.log
```

<img src='http://pycsp.googlecode.com/files/Screen%20shot%202010-10-29%20at%2010.50.00%20AM.png'>