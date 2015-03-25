

# Introduction #

The pycsp.parallel module has one any-2-any Channel type, which by default, allows other processes to connect to it. When a new channel is created, it is automatically hosted in the current Python interpreter. To connect to a hosted channel the location must be known, as there is no name server available for channels.

Every Python interpreter importing PyCSP.parallel will listen on only one port and that port handles all the communication to channels and processes started in this Python interpreter.

The default host is '0.0.0.0' and the default port is just any available port. To specify a host or port, the enviroment variables PYCSP\_HOST or PYCSP\_PORT may be used.

```
#This interpreter listens on port 8888 on localhost.
PYCSP_HOST=localhost PYCSP_PORT=8888 python test.py
```

```
#To connect to a channel 'A' on localhost, port 8888
A = pycsp.Channel('A', connect=('localhost, 8888))
```

# Connection Handling #

As all CSP communications are using sockets, it may happen that sockets is unable to connect or are disconnected unexpectedly. Such situations can be handled through catching the exceptions below.

| ChannelSocketException | The super class for the other Socket Exceptions |
|:-----------------------|:------------------------------------------------|
| ChannelConnectException(addr, msg) | This exception is raised when a channel is unable to connect to the destination provided in the connect parameter. |
| ChannelLostException |  This exception is raised when PyCSP has a channel which is left in an unstable state caused by a broken network connection, which could not be reestablished. Usually PyCSP can not recover from this exception. |
| ChannelBindException | This exception is raised when PyCSP is unable to bind to a port. |


Whenever a connection is lost, the connection is automatically recreated and retried. If after N tries, the connection still fails, then one of the above exceptions is raised.

## Latency hiding with a buffered channel ##

```
#Host A
import pycsp.parallel as pycsp
line42 = pycsp.Channel("line42", buffer=1000)
print("Address: %s" % (str(line42.address)))
input = line42.reader()
try:
  while True:
    data= input()
    # Perform work on data
except pycsp.ChannelRetireException:
  # Close hosted channel, as the channel has been retired
  pycsp.shutdown()
```


```
#Host B1,B2 .. BN
import pycsp.parallel as pycsp
line42 = pycsp.Channel("line42", connect=<address at Host A>)
output = line42.writer()
for i in xrange(10):
  output(i) # i could be large numpy arrays

pycsp.retire(output)

pycsp.shutdown()
```
## NAT traversal ##

For a process to communicate on a channel, it must be able to connect to the channel host. It is not necessary for the channel host, to be able to connect to the process, as the previous connection is used for two-way communication. Thus, if the relevant channels are hosted on points, which can be reached from multiple processes, these processes may communicate eventhough they can not connect directly to each other.

## Supported communication types ##

All channel configurations and all configurations for external choice is supported in a distributed environment as well as a local environment or any mix of the two.

## Limitations ##

  * All channel names have been restricted to a length of 32 chars.