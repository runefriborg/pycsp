# Multiple readers and writers #

Channels may have multiple readers or writers. It is not only legal, but also a very useful feature of CSP. The consistency lies in the model, which dictates that the writer is blocked until the message is received by exactly one reader.

```
@process
def source(chan_out):
    for i in range(10):
        chan_out("Hello world (%d)\n" % (i))
    retire(chan_out)
    
@process
def sink(chan_in):
    while True:
        sys.stdout.write(chan_in())

chan = Channel()
Parallel(
    5 * source(chan.writer()),
    5 * sink(chan.reader())
)
```

# Buffered Channels #

Channels in PyCSP are any-to-any and can be buffered.  To enable a buffer on a channel.

```
BufferC = Channel('A', buffer=3)
cout = BufferC.writer()
cin = BufferC.reader()
```

This channel has a buffer size of 3 and is semantically equivalent to a chain of 3 processes. It could be implemented like this:

```
@process
def BufferP(cin,cout):
  while True:
    cout(cin())

BufferC = Channel('A_buf')*4
for i in range(3):
  Spawn(
    BufferP(
      BufferC[i].reader(), BufferC[i+1].writer()
    )
  )
cout = BufferC[0].writer()
cin = BufferC[4].reader()
```

The use of buffered channels can be tricky, when used as output guards with AltSelect (external choice). The reason is that buffered channels are ready to receive messages until the buffer is full. To avoid starving other guards, buffered channels should be used as the last elements in a PriSelect or as an alternative the FairSelect can be used to balance the guards.


_In a distributed PyCSP application the buffer of a buffered channel is located where the Channel is hosted. Thus, hosting the Channel at the receiving end would enable some latency hiding by transferring the communicated data before a channel communication is committed._

# External Choice (AltSelect, PriSelect and FairSelect) #

The external choice selects a single guard from a set of guards. The different selection types are:

**AltSelect(G1, [G2, .. ,GN])** - The fastest choice, but does not guarantee priority. Guards are tested in the order they are given, but final selection may depend on other factors, such as network latency.

**PriSelect(G1, [G2, .. ,GN])** - Guarantees prioritised selection. Use PriSelect when using SkipGuards!

**FairSelect(G1, [G2, .. ,GN])** - Performs a fair selection by reordering guards based on previous choices and then executes a PriSelect on the new order of guards


The current guard types are:

```
* InputGuard(cin, action=[optional])
* OutputGuard(cout, msg=<message>, action=[optional])
* TimeoutGuard(seconds=<s>, action=[optional])
* SkipGuard(action=[optional])
```

where
```
cin = <chan>.reader()
cout = <chan>.writer()
```

AltSelect will perform a selection between the given guards. To select from multiple channels:

```
@process
def P1(cout, val):
  for i in range(5):
    cout(val)

A = Channel() * 2

@process
def P2(cin1, cin2):
  for i in range(10):
    g, msg = AltSelect(
      InputGuard(cin1),
      InputGuard(cin2)
    )
    if g == cin1:
      print 'Received',msg,'from chan1'
    else:
      print 'Received',msg,'from chan2'


Parallel(
  P1(A[0].writer(), 'Chan1'),
  P1(A[1].writer(), 'Chan2'),
  P2(A[0].reader(), A[1].reader())
)
```

Output:
```
Received Chan1 from chan1
Received Chan1 from chan1
Received Chan1 from chan1
Received Chan2 from chan2
Received Chan1 from chan1
Received Chan1 from chan1
Received Chan2 from chan2
Received Chan2 from chan2
Received Chan2 from chan2
Received Chan2 from chan2
```

Next we combine different guard types in a single guard set. Also you will notice that we have introduced the choice / action construct, which provide a means of attaching an action to a guard. This action is similar to a callback function and may be used to improve the structure of the code.

If it is necessary to modify variables in the namespace of a process calling AltSelect, then we recommend an if-then-else structure following the AltSelect.

```
@choice
def received_job(channel_input = None):
  save_result(channel_input)

@choice
def send_job(jobs, channel_input = None):
  jobs.pop()

while jobs or len(results) < jobcount:
  if jobs:
    AltSelect(
      InputGuard(workerIn, action=received_job),
      OutputGuard(workerOut, msg=jobs[-1],
				action=send_job(jobs)),
      TimeoutGuard(seconds=10, action=on_timeout)
    )
  else:
    received_job(workerIn())
```

Another example:

```
@choice
def on_timeout(channel_input = None):
  # handle timeout
  pass

ch_end, msg = AltSelect(
    InputGuard(workerIn),
    OutputGuard(workerOut, msg=jobs[-1]),
    TimeoutGuard(seconds=10, action=on_timeout)
)

if ch_end == workerIn:
  # perform action
elif ch_end == workerOut:
  # perform other action
```


Introducing the FairSelect:

```
@process
def writer(cout, id):
  while True:
    cout((id))

@process
def par_reader_fair(cinList, cnt):
  for i in range(cnt):
        
    c, msg = FairSelect(
            InputGuard(cinList[0]),
            InputGuard(cinList[1]),
            InputGuard(cinList[2]),
            InputGuard(cinList[3])
    )
            
    print 'From ',c ,'got',msg
  
  # Terminate
  poison(*cinList)

C=Channel('C') * 4
cnt = 10
    
Parallel(
  par_reader_fair([c.reader() for c in C], cnt),
  [ writer(C[id].writer(), id) for id in range(4)]
)
```

Output using FairSelect:

```
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x100426d50> named C> got 0
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x10070df90> named C1> got 1
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x100700090> named C2> got 2
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x100700110> named C3> got 3
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x100426d50> named C> got 0
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x10070df90> named C1> got 1
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x100700090> named C2> got 2
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x100700110> named C3> got 3
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x100426d50> named C> got 0
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x10070df90> named C1> got 1
```

Output using AltSelect:

```
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x10070df50> named C> got 0
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x10070df50> named C> got 0
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x100700550> named C1> got 1
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x10070df50> named C> got 0
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x10070df50> named C> got 0
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x10070df50> named C> got 0
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x10070df50> named C> got 0
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x100700550> named C1> got 1
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x100700190> named C2> got 2
From  <ChannelEndRead wrapping <pycsp.threads.channel.Channel object at 0x1007002d0> named C3> got 3
```