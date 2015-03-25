# Overview #




## Creating Processes ##
### @process ###

> @process decorator for creating process functions

```
    >>> @process
    ... def P():
    ...     pass
```

```
    >>> isinstance(P(), Process)
    True
```

## Starting Processes ##
### Parallel ###
> Parallel(P1, [P2, .. ,PN])

```
    >>> @process
    ... def P1(cout, id):
    ...     for i in range(10):
    ...         cout(id)
```

```
    >>> @process
    ... def P2(cin):
    ...     for i in range(10):
    ...         cin()
```

```
    >>> C = [Channel() for i in range(10)]
    >>> Cin = [chan.reader() for chan in C]
    >>> Cout = [chan.writer() for chan in C]
```

```
    >>> Parallel([P1(Cout[i], i) for i in range(10)],[P2(Cin[i]) for i in range(10)])
```

### Sequence ###
> Sequence(P1, [P2, .. ,PN])
> > The Sequence construct returns when all given processes exit.

```
    >>> @process
    ... def P1(cout):
    ...     Sequence([Process(cout,i) for i in range(10)])
```

```
    >>> C = Channel()
    >>> Spawn(P1(C.writer()))
```

```
    >>> L = []
    >>> cin = C.reader()
    >>> for i in range(10):
    ...    L.append(cin())
```

```
    >>> L
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

### Spawn ###

> Spawn(P1, [P2, .. ,PN])

```
    >>> @process
    ... def P1(cout, id):
    ...     for i in range(10):
    ...         cout(id)
```

```
    >>> C = Channel()
    >>> Spawn([P1(C.writer(), i) for i in range(10)])
```

```
    >>> L = []
    >>> cin = C.reader()
    >>> for i in range(100):
    ...    L.append(cin())
```

```
    >>> len(L)
    100
```

## Termination and Exceptions ##
### poison ###
> Poison channel

```
    >>> @process
    ... def P1(cin, done):
    ...     try:
    ...         while True:
    ...             cin()
    ...     except ChannelPoisonException:
    ...         done(42)
```

```
    >>> C1, C2 = Channel(), Channel()
    >>> Spawn(P1(C1.reader(), C2.writer()))
    >>> cout = C1.writer()
    >>> cout('Test')
```

```
    >>> poison(cout)
```

```
    >>> cin = C2.reader()
    >>> cin()
    42
```

### retire ###
> Retire reader or writer, to do auto-poisoning
> > When all readers or writer of a channel have retired. The channel is retired.

```
    >>> C = Channel()
    >>> cout1, cout2 = C.writer(), C.writer()
    >>> retire(cout1)
```

```
    >>> Spawn(Process(cout2, 'ok'))
```

```
    >>> try:
    ...     cout1('fail')
    ... except ChannelRetireException:
    ...     True
    True
```

```
    >>> cin = C.reader()
    >>> retire(cin)
```

## Channels ##

> Channel class.
> > Blocking or buffered communication.


```
    >>> @process
    ... def P1(cout):
    ...     while True:
    ...         cout('Hello World')
```

```
    >>> C = Channel()
    >>> Spawn(P1(C.writer()))
```

```
    >>> cin = C.reader()
    >>> cin()
    'Hello World'
```

```
    >>> retire(cin)
```


> Buffered channels are semantically equivalent with a chain
> of forwarding processes.
```
    >>> B = Channel(buffer=5)
    >>> cout = B.writer()
    >>> for i in range(5):
    ...     cout(i)
```

> Poison and retire are attached to final element of the buffer.
```
    >>> poison(cout)
```

```
    >>> @process
    ... def sink(cin, L):
    ...     while True:
    ...         L.append(cin())
```

```
    >>> L = []
    >>> Parallel(sink(B.reader(), L))
    >>> L
    [0, 1, 2, 3, 4]
```

### Joining to Read ###

> Join as reader

```
        >>> C = Channel()
        >>> cin = C.reader()
        >>> isinstance(cin, ChannelEndRead)
        True
```

### Joining to Write ###

> Join as writer

```
        >>> C = Channel()
        >>> cout = C.writer()
        >>> isinstance(cout, ChannelEndWrite)
        True
```

## External Choice / Choosing a Channel ##

> AltSelect is a wrapper to Alternation with a much more intuitive
> interface.
> It performs a prioritized choice from a list of guard objects and
> returns a tuple with the selected channel end and the read msg if
> there is one, otherwise None.


```
    >>> C = Channel()
    >>> cin = C.reader()
```

```
    >>> ch_end, msg = AltSelect(InputGuard(cin), SkipGuard())
```

```
    >>> if ch_end == cin:
    ...     print msg
    ... else:
    ...     print msg == None
    True
```


> AltSelect supports skip, timeout, input and output guards.

```
    >>> @choice 
    ... def callback(type, channel_input = None):
    ...    print type, channel_input
```

```
    >>> A, B = Channel('A'), Channel('B')
    >>> cin, cout = A.reader(), B.writer()
    >>> g1 = InputGuard(cin, action=callback('input'))
    >>> g2 = OutputGuard(cout, msg=[range(10),range(100)], action=callback('output'))
    >>> g3 = TimeoutGuard(seconds=0.1, action=callback('timeout'))
```

```
    >>> _ = AltSelect(g1, g2, g3)
    timeout None
```


> Note that AltSelect always performs the guard that was chosen,
> i.e. channel input or output is executed within the AltSelect so
> even the empty choice with an AltSelect or where
> the results are simply ignored, still performs the guarded input or
> output.

```
    >>> L = []
```

```
    >>> @choice 
    ... def action(channel_input):
    ...     L.append(channel_input)
```

```
    >>> @process
    ... def P1(cout, n=5):
    ...     for i in range(n):
    ...         cout(i)
```

```
    >>> @process
    ... def P2(cin1, cin2, n=10):
    ...     for i in range(n):
    ...         _ = AltSelect( InputGuard(cin1, action=action()), InputGuard(cin2, action=action()) )
```

```
    >>> C1, C2 = Channel(), Channel()
    >>> Parallel(P1(C1.writer()), P1(C2.writer()), P2(C1.reader(), C2.reader()))
```

```
    >>> len(L)
    10
```

```
    >>> L.sort()
    >>> L
    [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
```

### @choice ###

> Decorator for creating choice objets

```
    >>> @choice
    ... def action(channel_input=None):
    ...     print 'Hello'
```

```
    >>> _,_ = AltSelect(SkipGuard(action=action()))
    Hello
```

## Guards ##
### InputGuard ###

> InputGuard wraps an input ch\_end for use with AltSelect.


```
    >>> C = Channel()
    >>> cin, cout = C.reader(), C.writer()
```

```
    >>> @process
    ... def P1(cout):
    ...     for i in range(3): cout(i)
```

```
    >>> Spawn (P1(cout))
```

```
    >>> ch_end, msg = AltSelect( InputGuard(cin) )
    >>> ch_end, msg = AltSelect( InputGuard(cin, action="print channel_input") )
    1
```
```
    >>> ch_end, msg = AltSelect( InputGuard(cin, action=lambda channel_input: Spawn(Process(cout, channel_input))) )
```

```
    >>> @choice
    ... def Action(val1, val2, channel_input=None):
    ...     print channel_input
```

```
    >>> ch_end, msg = AltSelect( InputGuard(cin, action=Action('going into val1', 'going into val2')) )
    2
```

### OutputGuard ###

> OutputGuard wraps an output ch\_end for use with AltSelect.


```
    >>> C = Channel()
    >>> cin, cout = C.reader(), C.writer()
```

```
    >>> @process
    ... def P1(cin):
    ...     for i in range(5): cin()
```

```
    >>> Spawn (P1(cin))
```

```
    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=0) )
    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=1, action="print 'done'") )
    done
```

```
    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=2, action=lambda: Spawn(Process(cout, 3))) )
```

```
    >>> @choice
    ... def Action(val1, val2):
    ...     print 'sent'
```

```
    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=4, action=Action('going into val1', 'going into val2')) )
    sent
```

### SkipGuard ###

> SkipGuard will try to accept a read or a write, the moment it is posted.


```
    >>> C = Channel()
    >>> Cin = C.reader()
    >>> (g, msg) = AltSelect(InputGuard(Cin),  SkipGuard() )
```

```
    >>> isinstance(g, Skip) and msg == None
    True
```

### TimeoutGuard ###

> TimeoutGuard spawns a timer thread, when posted. If removed
> before timeout, then the timer thread is cancelled.

```
    >>> import time
```

```
    >>> C = Channel()
    >>> Cin = C.reader()
```

```
    >>> time_start = time.time()
    >>> (g, msg) = AltSelect( InputGuard(Cin), TimeoutGuard(seconds=0.5) )
    >>> time_passed = time.time() - time_start
```

```
    >>> time_passed >= 0.5
    True
```

```
    >>> time_passed < 0.6
    True
```

```
    >>> isinstance(g, Timeout) and msg == None
    True
```

## Specific for pycsp.greenlets: @io ##

> @io decorator for blocking io operations.
> Execution is moved to seperate threads and the current greenlet is yielded.


```
    >>> @io
    ... def sleep(n):
    ...     import time
    ...     time.sleep(n)
```

```
    >>> @process
    ... def P1():
    ...     sleep(0.05)
```

> Sleeping for 10 times 0.05 seconds, which equals roughly half a second
> in the sequential case.
```
    >>> time_start = time.time()
    >>> Sequence([P1() for i in range(10)])
    >>> diff = time.time() - time_start
    >>> diff >= 0.5 and diff < 0.6
    True
```

> In parallel, it should be close to 0.05 seconds.
```
    >>> time_start = time.time()
    >>> Parallel([P1() for i in range(10)])
    >>> diff = time.time() - time_start
    >>> diff >= 0.05 and diff < 0.1
    True
```
