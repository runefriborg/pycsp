# Channel Multiplier #
```
A = Channel('A') * <multiplier>
```

```
>>> A= Channel('A') * 3
>>> A[0].name
'A'
>>> A[1].name
'A1'
>>> A[2].name
'A2'
```

# Process Multiplier #

```
Parallel(
  P(<parameters>) * <multiplier>
)
```


```
>>> @process
... def P():
...     pass
... 
>>> P()
<Process(Thread-1, initial)>
>>> P() * 2
[<Process(Thread-2, initial)>, <Process(Thread-3, initial)>]
```

```
>>> @process
... def P():
...   print 'Hello', current_process_id()
... 
>>> Parallel(P() * 5)
Hello 0.2122764007741289306638.27
 Hello 0.3402057569491289306638.27
Hello 0.630868661511289306638.27
Hello 0.2323905151721289306638.27
 Hello 0.02407685114261289306638.27
```

When multiplying processes the argumentlist is traversed for channel ends and new channel ends are instantiated for new processes, to avoid having two processes referencing the same channel end.

```
@process
def P(cin):
  print current_process_id() + ' ' + str(cin())

chan = Channel('X')
Spawn(
  P(chan.reader(), ) * 10
)

cout = chan.writer()
for i in range(10):
  cout(i)
```

The above code produces the following output:

```
0.1083452839941289306925.94 1
0.9701965731871289306925.94 2
0.09972212802521289306925.94 0
0.08811378840181289306925.94 3
 0.9911784182721289306925.94 6
0.02519160333881289306925.94 5
0.7082968559831289306925.94 7
0.1502696612091289306925.94 8
 0.2164145215991289306925.94 4
0.9314496638651289306925.94 9
```

# Reader (+) and Writer (-) #

```
>>> A = Channel()
>>> +A
<ChannelEndRead ...>
>>> -A
<ChannelEndWrite ...>
```

replacing

```
>>> A = Channel()
>>> A.reader()
<ChannelEndRead ...>
>>> A.writer()
<ChannelEndWrite ...>
```

In use:

```
chan = Channel()
Parallel(
  P1(+chan)
  P2(-chan)
)
```