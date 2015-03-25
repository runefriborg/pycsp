# Termination #

```
import pycsp.parallel as pycsp

C = pycsp.Channel()
@pycsp.process
def P(cin):
  while True:
    val = cin()
    ...

pycsp.Spawn(P(C.reader())
```

Shutdown on next read.

```
  pycsp.poison(cin)
```

Exception handling:
```
import pycsp.parallel as pycsp

@pycsp.process
def streamFile(cout, filename):
  try:
    f = open(filename)
    lock(f)
    ...
  except pycsp.ChannelPoisonException:
    unlock(f)
    f.close()
```