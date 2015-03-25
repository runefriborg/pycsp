
# <pre>Process</pre> #
## <pre>@process</pre> ##
<pre>
Help on function process in module pycsp.parallel.process:<br>
<br>
process(func)<br>
@process decorator for making a function into a CSP Process factory.<br>
Each generated CSP process is implemented as a single OS thread.<br>
<br>
Usage:<br>
>>> @process<br>
>>> def filter(dataIn, dataOut, tag, debug=False):<br>
>>>   pass # perform filtering<br>
>>><br>
>>> P = filter(A.reader(), B.writer(), "42", debug=True)<br>
<br>
The CSP Process factory returned by the @process decorator:<br>
func(*args, **kwargs)<br>
<br>
</pre>
## <pre>Process</pre> ##
<pre>
Help on class Process in module pycsp.parallel.process:<br>
<br>
class Process(threading.Thread)<br>
|  Process(func, *args, **kwargs)<br>
|<br>
|  CSP process implemented as a single OS thread.<br>
|<br>
|  It is recommended to use the @process decorator, to create Process instances.<br>
|  See help(pycsp.process)<br>
|<br>
|  Usage:<br>
|    >>> def filter(dataIn, dataOut, tag, debug=False):<br>
|    >>>   pass # perform filtering<br>
|    >>><br>
|    >>> P = Process(filter, A.reader(), B.writer(), "42", debug=True)<br>
|<br>
|  Process(func, *args, **kwargs)<br>
|  func<br>
|    The function object to wrap and execute in the body of the process.<br>
|  args and kwargs<br>
|    are passed directly to the execution of the function object.<br>
|<br>
|  Public variables:<br>
|    Process.name       Unique name to identify the process<br>
|<br>
|  Method resolution order:<br>
|      Process<br>
|      threading.Thread<br>
|      threading._Verbose<br>
|      __builtin__.object<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __init__(self, fn, *args, **kwargs)<br>
|<br>
|  __mul__(self, multiplier)<br>
|      # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]<br>
|<br>
|  __rmul__(self, multiplier)<br>
|      # syntactic sugar:  2 * Process() == [Process<1>,Process<2>]<br>
|<br>
|  join_report(self)<br>
|<br>
|  run(self)<br>
|<br>
|  update(self, **kwargs)<br>
|<br>
|  wait(self)<br>
|<br>
|  wait_ack(self)<br>
|<br>
|  ----------------------------------------------------------------------<br>
|  Methods inherited from threading.Thread:<br>
|<br>
|  __repr__(self)<br>
|<br>
|  getName(self)<br>
|<br>
|  isAlive(self)<br>
|<br>
|  isDaemon(self)<br>
|<br>
|  is_alive = isAlive(self)<br>
|<br>
|  join(self, timeout=None)<br>
|<br>
|  setDaemon(self, daemonic)<br>
|<br>
|  setName(self, name)<br>
|<br>
|  start(self)<br>
|<br>
|  ----------------------------------------------------------------------<br>
|  Data descriptors inherited from threading.Thread:<br>
|<br>
|  daemon<br>
|<br>
|  ident<br>
|<br>
|  name<br>
|<br>
|  ----------------------------------------------------------------------<br>
|  Data descriptors inherited from threading._Verbose:<br>
|<br>
|  __dict__<br>
|      dictionary for instance variables (if defined)<br>
|<br>
|  __weakref__<br>
|      list of weak references to the object (if defined)<br>
<br>
</pre>
## <pre>@multiprocess</pre> ##
<pre>
Help on function multiprocess in module pycsp.parallel.multiprocess:<br>
<br>
multiprocess(func=None, pycsp_host='', pycsp_port=None)<br>
@multiprocess(pycsp_host='', pycsp_port=None)<br>
<br>
@multiprocess decorator for making a function into a CSP MultiProcess factory.<br>
Each generated CSP process is implemented as a single OS process.<br>
<br>
All objects and variables provided to multiprocesses through the<br>
parameter list must support pickling.<br>
<br>
Usage:<br>
>>> @multiprocess<br>
>>> def filter(dataIn, dataOut, tag, debug=False):<br>
>>>   pass # perform filtering<br>
>>><br>
>>> P = filter(A.reader(), B.writer(), "42", debug=True)<br>
<br>
or<br>
>>> @multiprocess(pycsp_host="localhost", pycsp_port=9998)<br>
>>> def filter(dataIn, dataOut, tag, debug=False):<br>
>>>   pass # perform filtering<br>
>>><br>
>>> P = filter(A.reader(), B.writer(), "42", debug=True)<br>
<br>
The CSP MultiProcess factory returned by the @multiprocess decorator:<br>
func(*args, **kwargs)<br>
<br>
</pre>
## <pre>MultiProcess</pre> ##
<pre>
Help on class MultiProcess in module pycsp.parallel.multiprocess:<br>
<br>
class MultiProcess(multiprocessing.process.Process)<br>
|  MultiProcess(func, *args, **kwargs)<br>
|<br>
|  CSP process implemented as a single OS process.<br>
|<br>
|  It is recommended to use the @multiprocess decorator, to create MultiProcess instances.<br>
|  See help(pycsp.multiprocess)<br>
|<br>
|  Usage:<br>
|    >>> def filter(dataIn, dataOut, tag, debug=False):<br>
|    >>>   pass # perform filtering<br>
|    >>><br>
|    >>> P = MultiProcess(filter, A.reader(), B.writer(), "42", debug=True, pycsp_host='localhost')<br>
|<br>
|  MultiProcess(func, *args, **kwargs)<br>
|  func<br>
|    The function object to wrap and execute in the body of the process.<br>
|  args and kwargs<br>
|    are pickled and sent to the multiprocess where it is reassembled and<br>
|    passed to the execution of the function object.<br>
|<br>
|  Public variables:<br>
|    MultiProcess.name       Unique name to identify the process<br>
|<br>
|  Method resolution order:<br>
|      MultiProcess<br>
|      multiprocessing.process.Process<br>
|      __builtin__.object<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __init__(self, fn, *args, **kwargs)<br>
|<br>
|  __mul__(self, multiplier)<br>
|      # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]<br>
|<br>
|  __rmul__(self, multiplier)<br>
|      # syntactic sugar:  2 * Process() == [Process<1>,Process<2>]<br>
|<br>
|  join_report(self)<br>
|<br>
|  run(self)<br>
|<br>
|  update(self, **kwargs)<br>
|<br>
|  wait(self)<br>
|<br>
|  wait_ack(self)<br>
|<br>
|  ----------------------------------------------------------------------<br>
|  Methods inherited from multiprocessing.process.Process:<br>
|<br>
|  __repr__(self)<br>
|<br>
|  is_alive(self)<br>
|      Return whether process is alive<br>
|<br>
|  join(self, timeout=None)<br>
|      Wait until child process terminates<br>
|<br>
|  start(self)<br>
|      Start child process<br>
|<br>
|  terminate(self)<br>
|      Terminate process; sends SIGTERM signal or uses TerminateProcess()<br>
|<br>
|  ----------------------------------------------------------------------<br>
|  Data descriptors inherited from multiprocessing.process.Process:<br>
|<br>
|  __dict__<br>
|      dictionary for instance variables (if defined)<br>
|<br>
|  __weakref__<br>
|      list of weak references to the object (if defined)<br>
|<br>
|  authkey<br>
|<br>
|  daemon<br>
|      Return whether process is a daemon<br>
|<br>
|  exitcode<br>
|      Return exit code of process or None if it has yet to stop<br>
|<br>
|  ident<br>
|      Return identifier (PID) of process or None if it has yet to start<br>
|<br>
|  name<br>
|<br>
|  pid<br>
|      Return identifier (PID) of process or None if it has yet to start<br>
<br>
</pre>
# <pre>Remote Process</pre> #
## <pre>@sshprocess</pre> ##
<pre>
Help on function sshprocess in module pycsp.parallel.sshprocess:<br>
<br>
sshprocess(func=None, pycsp_host='', pycsp_port=0, ssh_host='localhost', ssh_port=22, ssh_user=None, ssh_password=None, ssh_python='python')<br>
@sshprocess(pycsp_host='', pycsp_port=0, ssh_host='localhost', ssh_port=22, ssh_user=None, ssh_password=None, ssh_python='python')<br>
<br>
This may be used to create a CSP network spanning remote hosts.<br>
Create CSP processes running in a new Python interpreter started on a remote host using the<br>
SSH2 protocol (paramiko module)<br>
<br>
It is not recommended to use the password argument. Instead, setup the remote host<br>
for a passwordless login using private/public key authorisation.<br>
<br>
<br>
@sshprocess decorator for making a function into a CSP SSHProcess factory.<br>
<br>
All objects and variables provided to sshprocesses through the<br>
parameter list must support pickling.<br>
<br>
Usage:<br>
>>> @sshprocess(ssh_host="10.22.32.10")<br>
>>> def filter(dataIn, dataOut, tag, debug=False):<br>
>>>   pass # perform filtering<br>
>>><br>
>>> P = filter(A.reader(), B.writer(), "42", debug=True)<br>
<br>
or<br>
>>> @sshprocess(ssh_host="10.0.10.1", ssh_user="guest", ssh_password="42", ssh_python='python-2.6')<br>
>>> def filter(dataIn, dataOut, tag, debug=False):<br>
>>>   pass # perform filtering<br>
>>><br>
>>> P = filter(A.reader(), B.writer(), "42", debug=True)<br>
<br>
The CSP SSHProcess factory returned by the @sshprocess decorator:<br>
func(*args, **kwargs)<br>
<br>
</pre>
## <pre>SSHProcess</pre> ##
<pre>
Help on class SSHProcess in module pycsp.parallel.sshprocess:<br>
<br>
class SSHProcess(__builtin__.object)<br>
|  SSHProcess(func, *args, **kwargs)<br>
|<br>
|  This may be used to create a CSP network spanning remote hosts.<br>
|  Create CSP processes running in a new Python interpreter started on a remote host using the<br>
|  SSH2 protocol (paramiko module)<br>
|<br>
|  It is recommended to use the @sshprocess decorator, to create SSHProcess instances.<br>
|  See help(pycsp.sshprocess)<br>
|<br>
|  Usage:<br>
|    >>> def filter(dataIn, dataOut, tag, debug=False):<br>
|    >>>   pass # perform filtering<br>
|    >>><br>
|    >>> P = SSHProcess(filter, A.reader(), B.writer(), "42", debug=True, ssh_host='10.0.0.2', ssh_python='python-2.7')<br>
|<br>
|  SSHProcess(func, *args, **kwargs)<br>
|  func<br>
|    The function object to wrap and execute in the body of the process.<br>
|  args and kwargs<br>
|    are pickled and sent to the multiprocess where it is reassembled and<br>
|    passed to the execution of the function object.<br>
|<br>
|  Public variables:<br>
|    SSHProcess.name       Unique name to identify the process<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __init__(self, fn, *args, **kwargs)<br>
|<br>
|  __mul__(self, multiplier)<br>
|      # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]<br>
|<br>
|  __rmul__(self, multiplier)<br>
|      # syntactic sugar:  2 * Process() == [Process<1>,Process<2>]<br>
|<br>
|  join_report(self)<br>
|<br>
|  start(self)<br>
|<br>
|  update(self, **kwargs)<br>
|<br>
|  ----------------------------------------------------------------------<br>
|  Data descriptors defined here:<br>
|<br>
|  __dict__<br>
|      dictionary for instance variables (if defined)<br>
|<br>
|  __weakref__<br>
|      list of weak references to the object (if defined)<br>
<br>
</pre>
## <pre>@clusterprocess</pre> ##
<pre>
Help on function clusterprocess in module pycsp.parallel.clusterprocess:<br>
<br>
clusterprocess(func=None, cluster_nodefile='$PBS_NODEFILE', cluster_pin=None, cluster_hint='blocked', cluster_ssh_port=22, cluster_python='python')<br>
@clusterprocess(cluster_nodefile="", cluster_pin=None, cluster_hint='blocked', cluster_ssh_port=22, cluster_python='python')<br>
<br>
This may be used to create a CSP network spanning remote hosts provided in a nodefile.<br>
<br>
Example of a 'nodefile':<br>
node1.host.org<br>
node1.host.org<br>
node2.host.org<br>
node2.host.org<br>
<br>
The location of this nodefile may then be provided using the Environment variable $PBS_NODEFILE.<br>
<br>
cluster_pin=X is used to pin a process to Xth entry in the nodefile.<br>
<br>
cluster_hint=[ 'blocked', 'strided', 'local' ] selects a distribution scheme for processes.<br>
<br>
All objects and variables provided to clusterprocesses through the<br>
parameter list must support pickling.<br>
<br>
Usage:<br>
>>> @clusterprocess<br>
>>> def filter(dataIn, dataOut, tag, debug=False):<br>
>>>   pass # perform filtering<br>
>>><br>
>>> P = filter(A.reader(), B.writer(), "42", debug=True)<br>
<br>
or<br>
>>> @clusterprocess(cluster_hint="local")<br>
>>> def filter(dataIn, dataOut, tag, debug=False):<br>
>>>   pass # perform filtering<br>
>>><br>
>>> P = filter(A.reader(), B.writer(), "42", debug=True)<br>
<br>
The cluster_* variables may overwritten in Parallel/Sequence/Spawn<br>
>>> Parallel(P, cluster_hint='blocked')<br>
<br>
The CSP ClusterProcess factory returned by the @clusterprocess decorator:<br>
func(*args, **kwargs)<br>
<br>
</pre>
## <pre>ClusterProcess</pre> ##
<pre>
Help on class ClusterProcess in module pycsp.parallel.clusterprocess:<br>
<br>
class ClusterProcess(__builtin__.object)<br>
|  ClusterProcess(func, *args, **kwargs)<br>
|<br>
|  This may be used to create a CSP network spanning remote hosts.<br>
|<br>
|  It is recommended to use the @clusterprocess decorator, to create ClusterProcess instances.<br>
|  See help(pycsp.clusterprocess)<br>
|<br>
|  Usage:<br>
|    >>> def filter(dataIn, dataOut, tag, debug=False):<br>
|    >>>   pass # perform filtering<br>
|    >>><br>
|    >>> P = ClusterProcess(filter, A.reader(), B.writer(), "42", debug=True, cluster_pin=1)<br>
|<br>
|  ClusterProcess(func, *args, **kwargs)<br>
|  func<br>
|    The function object to wrap and execute in the body of the process.<br>
|  args and kwargs<br>
|    are pickled and sent to the multiprocess where it is reassembled and<br>
|    passed to the execution of the function object.<br>
|<br>
|  Public variables:<br>
|    ClusterProcess.name       Unique name to identify the process<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __init__(self, fn, *args, **kwargs)<br>
|<br>
|  __mul__(self, multiplier)<br>
|      # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]<br>
|<br>
|  __rmul__(self, multiplier)<br>
|      # syntactic sugar:  2 * Process() == [Process<1>,Process<2>]<br>
|<br>
|  join_report(self)<br>
|<br>
|  start(self)<br>
|<br>
|  update(self, **kwargs)<br>
|<br>
|  ----------------------------------------------------------------------<br>
|  Data descriptors defined here:<br>
|<br>
|  __dict__<br>
|      dictionary for instance variables (if defined)<br>
|<br>
|  __weakref__<br>
|      list of weak references to the object (if defined)<br>
<br>
</pre>
# <pre>Process Execution</pre> #
## <pre>Parallel</pre> ##
<pre>
Help on function Parallel in module pycsp.parallel.process:<br>
<br>
Parallel(*plist, **kwargs)<br>
Parallel(P1, [P2, .. ,PN])<br>
<br>
Performs concurrent synchronous execution of the supplied CSP processes.<br>
<br>
Blocks until all processes have exited.<br>
<br>
Usage:<br>
>>> @process<br>
... def P1(cout):<br>
...     for i in range(10):<br>
...         cout(i)<br>
...     retire(cout)<br>
<br>
>>> @process<br>
... def P2(cin):<br>
...     while True:<br>
...         cin()<br>
<br>
>>> C = Channel()<br>
>>> Parallel(P1(C.writer()), P2(C.reader()))<br>
<br>
</pre>
## <pre>Spawn</pre> ##
<pre>
Help on function Spawn in module pycsp.parallel.process:<br>
<br>
Spawn(*plist, **kwargs)<br>
Spawn(P1, [P2, .. ,PN])<br>
<br>
Performs concurrent asynchronous execution of the supplied CSP processes.<br>
<br>
Usage:<br>
>>> @process<br>
... def P1(cout):<br>
...     for i in range(10):<br>
...         cout(i)<br>
...     retire(cout)<br>
<br>
>>> C = Channel()<br>
>>> Parallel(P1(C.writer()))<br>
<br>
>>> cin = C.reader()<br>
... try:<br>
...     while True:<br>
...         cin()<br>
<br>
</pre>
## <pre>Sequence</pre> ##
<pre>
Help on function Sequence in module pycsp.parallel.process:<br>
<br>
Sequence(*plist, **kwargs)<br>
Sequence(P1, [P2, .. ,PN])<br>
<br>
Performs synchronous execution of the supplied CSP processes.<br>
<br>
The supplied processes are executed in order.<br>
<br>
Blocks until the last process has exited.<br>
<br>
Usage:<br>
>>> @process<br>
... def P1(id):<br>
...     print(id)<br>
<br>
>>> L = [P1(i) for i in range(10)]<br>
>>> Sequence(L)<br>
<br>
</pre>
# <pre>Channel</pre> #
## <pre>Channel</pre> ##
<pre>
Help on class Channel in module pycsp.parallel.channel:<br>
<br>
class Channel(__builtin__.object)<br>
|  Channel(name=None, buffer=0, connect=None)<br>
|<br>
|  Any-2-any channel for communication between both local and remote processes.<br>
|<br>
|  To communicate on this channel, channel ends must be requested using the .reader/.writer methods.<br>
|<br>
|  Usage:<br>
|    >>> A = Channel("A")<br>
|    >>> cout = A.writer()<br>
|    >>> cout("Hello World")<br>
|<br>
|  A channel is registered at the Python interpreter level and hosted in the interpreter where it<br>
|  was created.<br>
|<br>
|  Retrieving the address and name of a channel:<br>
|  >>> print(A.address)<br>
|  ('10.11.105.254', 33703)<br>
|  >>> print(A.name)<br>
|  A<br>
|<br>
|  Channel(name=None, buffer=0, connect=None):<br>
|  name<br>
|    is a string used for identifying the Channel and must be unique for every Channel instance.<br>
|    The name is limited to maximum 32 characters. If name=None then a unique name is generated.<br>
|  buffer<br>
|    The channel may be buffered by configuring a buffer of size <buffer>.<br>
|    buffer=3 will create a channel which can contain three elements, before blocking send.<br>
|  connect<br>
|    If provided with (host, port), the channel will not create a host, but instead try to connect<br>
|    to (host, port) and register at the channel here.<br>
|    A name must be provided when connect is set.<br>
|<br>
|  Public variables:<br>
|    Channel.address    (host, port) where the channel is hosted<br>
|    Channel.name       name to identify the hosted channel<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __init__(self, name=None, buffer=0, connect=None)<br>
|      # Constructor<br>
|<br>
|  __mul__(self, multiplier)<br>
|      # syntactic sugar: Channel() * N<br>
|<br>
|  __neg__(self)<br>
|      # syntactic sugar: cout = -chan<br>
|<br>
|  __pos__(self)<br>
|      # syntactic sugar: cin = +chan<br>
|<br>
|  __rmul__(self, multiplier)<br>
|      # syntactic sugar: N * Channel()<br>
|<br>
|  disconnect(self)<br>
|      Explicit close is only relevant for channel references<br>
|      connected to remote channels<br>
|<br>
|      It can be used to make an early close, to allow another interpreter<br>
|      hosting the channel home, to quit. This is especially useful when<br>
|      used in a server - client setting, where the client has provied a<br>
|      reply channel and desires to disconnect after having received the reply.<br>
|<br>
|      The channel reference will automatically open and reconnect if it is used after a close.<br>
|<br>
|  reader(self)<br>
|      Create and return a receiving end of the channel<br>
|<br>
|      Returns:<br>
|        ChannelEndRead object<br>
|<br>
|      Usage:<br>
|        >>> C = Channel()<br>
|        >>> cin = C.reader()<br>
|        >>> print( cin() ) # Read<br>
|<br>
|  writer(self)<br>
|      Create and return a writing end of the channel<br>
|<br>
|      Returns:<br>
|        ChannelEndWrite object<br>
|<br>
|      Usage:<br>
|        >>> C = Channel()<br>
|        >>> cout = C.writer()<br>
|        >>> cout("Hello reader")<br>
|<br>
|  ----------------------------------------------------------------------<br>
|  Data descriptors defined here:<br>
|<br>
|  __dict__<br>
|      dictionary for instance variables (if defined)<br>
|<br>
|  __weakref__<br>
|      list of weak references to the object (if defined)<br>
<br>
</pre>
## <pre>ChannelEndRead</pre> ##
<pre>
Help on instance of ChannelEndRead in module pycsp.parallel.channel:<br>
<br>
class ChannelEndRead(ChannelEnd)<br>
|  The reading end of a channel.<br>
|<br>
|  Usage:<br>
|    >>> val = reading_end()<br>
|<br>
|  Throws:<br>
|    ChannelPoisonException()<br>
|    ChannelRetireException()<br>
|<br>
|  If the poison and retire exceptions are not caught explicitly they will automatically be<br>
|  propagated to all other known channelends provided to the process in the argument list.<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __call__(self)<br>
|<br>
|  __init__(self, channel)<br>
|<br>
|  __repr__(self)<br>
|<br>
|  ----------------------------------------------------------------------<br>
|  Methods inherited from ChannelEnd:<br>
|<br>
|  __getstate__(self)<br>
|      Enables channel end mobility<br>
|<br>
|  __setstate__(self, dict)<br>
|      Enables channel end mobility<br>
|<br>
|  disconnect(self)<br>
|      Explicit close is only relevant for mobile channel ends to invoke an<br>
|      early close.<br>
|<br>
|      The reason for an early close is to allow another interpreter<br>
|      hosting the channel home, to quit. This is especially useful when<br>
|      used in a server/client setting, where the client has provided a<br>
|      reply channel and desires to disconnect after having received the reply.<br>
|<br>
|      The mobile channel end reference will automatically open and reconnect if<br>
|      it is used after a close.<br>
|<br>
|  isReader(self)<br>
|      Returns True for ChannelEndRead object<br>
|<br>
|  isWriter(self)<br>
|      Returns True for ChannelEndWrite object<br>
|<br>
|  poison(self)<br>
|      Poison channel end<br>
|<br>
|      When a channel end is poisoned, the channel is set into a poisoned state where<br>
|      after all actions on the channel will invoke a ChannelPoisonException which<br>
|      is propagated through the PyCSP network to shutdown all processes unless<br>
|      caugth by the user with a try/except clause.<br>
|<br>
|      Notice that poisoning may cause race conditions, when terminating multiple concurrent processes.<br>
|      See retire for an improved shutdown method.<br>
|<br>
|  retire(self)<br>
|      Retire channel end<br>
|<br>
|      When a channel end is retired, the channel is signaled that a channel end<br>
|      has now left the channel. When the set of all reading or writing channel ends is set<br>
|      to none, then the channel enters a retired state whereafter<br>
|      all actions on the channel will invoke a ChannelRetireException which<br>
|      is propagated through the PyCSP network to nicely shutdown all processes unless<br>
|      caugth by the user with a try/except clause.<br>
|<br>
|      Retiring is an improved version of poisoning, which avoids the race condition issue<br>
|      when terminating multiple concurrent processes.<br>
<br>
</pre>
## <pre>ChannelEndWrite</pre> ##
<pre>
Help on instance of ChannelEndWrite in module pycsp.parallel.channel:<br>
<br>
class ChannelEndWrite(ChannelEnd)<br>
|  Methods defined here:<br>
|<br>
|  __call__(self, msg)<br>
|<br>
|  __init__(self, channel)<br>
|<br>
|  __repr__(self)<br>
|<br>
|  ----------------------------------------------------------------------<br>
|  Methods inherited from ChannelEnd:<br>
|<br>
|  __getstate__(self)<br>
|      Enables channel end mobility<br>
|<br>
|  __setstate__(self, dict)<br>
|      Enables channel end mobility<br>
|<br>
|  disconnect(self)<br>
|      Explicit close is only relevant for mobile channel ends to invoke an<br>
|      early close.<br>
|<br>
|      The reason for an early close is to allow another interpreter<br>
|      hosting the channel home, to quit. This is especially useful when<br>
|      used in a server/client setting, where the client has provided a<br>
|      reply channel and desires to disconnect after having received the reply.<br>
|<br>
|      The mobile channel end reference will automatically open and reconnect if<br>
|      it is used after a close.<br>
|<br>
|  isReader(self)<br>
|      Returns True for ChannelEndRead object<br>
|<br>
|  isWriter(self)<br>
|      Returns True for ChannelEndWrite object<br>
|<br>
|  poison(self)<br>
|      Poison channel end<br>
|<br>
|      When a channel end is poisoned, the channel is set into a poisoned state where<br>
|      after all actions on the channel will invoke a ChannelPoisonException which<br>
|      is propagated through the PyCSP network to shutdown all processes unless<br>
|      caugth by the user with a try/except clause.<br>
|<br>
|      Notice that poisoning may cause race conditions, when terminating multiple concurrent processes.<br>
|      See retire for an improved shutdown method.<br>
|<br>
|  retire(self)<br>
|      Retire channel end<br>
|<br>
|      When a channel end is retired, the channel is signaled that a channel end<br>
|      has now left the channel. When the set of all reading or writing channel ends is set<br>
|      to none, then the channel enters a retired state whereafter<br>
|      all actions on the channel will invoke a ChannelRetireException which<br>
|      is propagated through the PyCSP network to nicely shutdown all processes unless<br>
|      caugth by the user with a try/except clause.<br>
|<br>
|      Retiring is an improved version of poisoning, which avoids the race condition issue<br>
|      when terminating multiple concurrent processes.<br>
<br>
</pre>
## <pre>ChannelConnectException</pre> ##
<pre>
ChannelConnectException(addr, msg)<br>
<br>
This exception is raised when a channel is unable to connect<br>
to the destination provided in the connect parameter.<br>
<br>
Usage:<br>
>>> try:<br>
...     A = Channel('A', connect=('unknown', 999))<br>
... except ChannelConnectException as e:<br>
...     print("Addr %s is unavailable<br>
", % (str(e.addr)))<br>
<br>
If a mobile channel end is sent to another remote interpreter, where<br>
the channel end is unable to reconnect with the channel host, then<br>
a ChannelConnectException is also raised.<br>
<br>
</pre>
## <pre>ChannelBindException</pre> ##
<pre>
ChannelBindException(addr, msg)<br>
<br>
This exception is raised when PyCSP is unable to bind to a port.<br>
<br>
The host and port to bind to is ('', 0) which binds<br>
to 0.0.0.0 and any available port number, unless provided through<br>
environment variables, configuration variables or from parameters<br>
to multiprocess.<br>
<br>
Usage:<br>
>>> @multiprocess(port=99)<br>
... def runner(chanName):<br>
...     A = Channel(chanName)<br>
...     cin = A.reader()<br>
...     print(cin())<br>
<br>
>>> try:<br>
...     Parallel(runner('A'))<br>
... except ChannelBindException:<br>
...     print("Can not bind to port 80")<br>
<br>
</pre>
## <pre>ChannelLostException</pre> ##
<pre>
ChannelLostException(addr, msg)<br>
<br>
This exception is raised when PyCSP has a channel which is left<br>
in an unstable state caused by a broken network connection, which<br>
could not be reestablished.<br>
<br>
Usually PyCSP can not recover from this exception.<br>
<br>
</pre>
# <pre>AltSelect</pre> #
## <pre>AltSelect</pre> ##
<pre>
Help on function AltSelect in module pycsp.parallel.altselect:<br>
<br>
AltSelect(*guards)<br>
AltSelect(G1, [G2, .. ,GN])<br>
<br>
AltSelect performs a fast choice from a list of guard objects and<br>
returns a tuple with the selected channel end and the read msg if<br>
there is one, otherwise None.<br>
<br>
Usage:<br>
>>> g,msg = AltSelect(InputGuard(cin1), InputGuard(cin2))<br>
>>> print("Message:%s" % (str(msg)))<br>
<br>
Returns:<br>
ChannelEnd, message<br>
<br>
More detailed usage:<br>
<br>
AltSelect supports skip, timeout, input and output guards. Though,<br>
it is recommended to use the slightly slower PriSelect when using<br>
skip guards.<br>
<br>
>>> @choice<br>
... def callback(type, channel_input = None):<br>
...    print type, channel_input<br>
<br>
>>> A, B = Channel('A'), Channel('B')<br>
>>> cin, cout = A.reader(), B.writer()<br>
>>> g1 = InputGuard(cin, action=callback('input'))<br>
>>> g2 = OutputGuard(cout, msg=[range(10),range(100)], action=callback('output'))<br>
>>> g3 = TimeoutGuard(seconds=0.1, action=callback('timeout'))<br>
<br>
>>> _ = AltSelect(g1, g2, g3)<br>
timeout None<br>
<br>
<br>
Note that AltSelect always performs the guard that was chosen,<br>
i.e. channel input or output is executed within the AltSelect so<br>
even the empty choice with an AltSelect or where<br>
the results are simply ignored, still performs the guarded input or<br>
output.<br>
<br>
>>> L = []<br>
<br>
>>> @choice<br>
... def action(channel_input):<br>
...     L.append(channel_input)<br>
<br>
>>> @process<br>
... def P1(cout, n=5):<br>
...     for i in range(n):<br>
...         cout(i)<br>
<br>
>>> @process<br>
... def P2(cin1, cin2, n=10):<br>
...     for i in range(n):<br>
...         _ = AltSelect( InputGuard(cin1, action=action()), InputGuard(cin2, action=action()) )<br>
<br>
>>> C1, C2 = Channel(), Channel()<br>
>>> Parallel(P1(C1.writer()), P1(C2.writer()), P2(C1.reader(), C2.reader()))<br>
<br>
>>> len(L)<br>
10<br>
<br>
>>> L.sort()<br>
>>> L<br>
[0, 0, 1, 1, 2, 2, 3, 3, 4, 4]<br>
<br>
</pre>
## <pre>PriSelect</pre> ##
<pre>
Help on function PriSelect in module pycsp.parallel.altselect:<br>
<br>
PriSelect(*guards)<br>
PriSelect(G1, [G2, .. ,GN])<br>
<br>
PriSelect performs a prioritized choice from a list of guard objects and<br>
returns a tuple with the selected channel end and the read msg if<br>
there is one, otherwise None.<br>
<br>
Usage:<br>
>>> g,msg = PriSelect(InputGuard(cin1), InputGuard(cin2))<br>
>>> print("Message:%s" % (str(msg)))<br>
<br>
Returns:<br>
ChannelEnd, message<br>
<br>
More detailed usage:<br>
>>> C = Channel()<br>
>>> cin = C.reader()<br>
<br>
>>> ch_end, msg = PriSelect(InputGuard(cin), SkipGuard())<br>
<br>
>>> if ch_end == cin:<br>
...     print msg<br>
... else:<br>
...     print msg == None<br>
True<br>
<br>
<br>
PriSelect supports skip, timeout, input and output guards.<br>
<br>
>>> @choice<br>
... def callback(type, channel_input = None):<br>
...    print type, channel_input<br>
<br>
>>> A, B = Channel('A'), Channel('B')<br>
>>> cin, cout = A.reader(), B.writer()<br>
>>> g1 = InputGuard(cin, action=callback('input'))<br>
>>> g2 = OutputGuard(cout, msg=[range(10),range(100)], action=callback('output'))<br>
>>> g3 = TimeoutGuard(seconds=0.1, action=callback('timeout'))<br>
<br>
>>> _ = PriSelect(g1, g2, g3)<br>
timeout None<br>
<br>
<br>
Note that PriSelect always performs the guard that was chosen,<br>
i.e. channel input or output is executed within the PriSelect so<br>
even the empty choice with an PriSelect or where<br>
the results are simply ignored, still performs the guarded input or<br>
output.<br>
<br>
>>> L = []<br>
<br>
>>> @choice<br>
... def action(channel_input):<br>
...     L.append(channel_input)<br>
<br>
>>> @process<br>
... def P1(cout, n=5):<br>
...     for i in range(n):<br>
...         cout(i)<br>
<br>
>>> @process<br>
... def P2(cin1, cin2, n=10):<br>
...     for i in range(n):<br>
...         _ = PriSelect( InputGuard(cin1, action=action()), InputGuard(cin2, action=action()) )<br>
<br>
>>> C1, C2 = Channel(), Channel()<br>
>>> Parallel(P1(C1.writer()), P1(C2.writer()), P2(C1.reader(), C2.reader()))<br>
<br>
>>> len(L)<br>
10<br>
<br>
>>> L.sort()<br>
>>> L<br>
[0, 0, 1, 1, 2, 2, 3, 3, 4, 4]<br>
<br>
</pre>
## <pre>FairSelect</pre> ##
<pre>
Help on function FairSelect in module pycsp.parallel.altselect:<br>
<br>
FairSelect(*guards)<br>
FairSelect(G1, [G2, .. ,GN])<br>
<br>
FairSelect sorts the list of guards in order based on the history for<br>
the chosen guards in this FairSelect.<br>
<br>
Internally it invokes a priority select on the new order of guards.<br>
<br>
Timer and Skip guards are always given lowest priority.<br>
<br>
Usage:<br>
>>> g,msg = FairSelect(InputGuard(cin1), InputGuard(cin2))<br>
>>> print("Message:%s" % (str(msg)))<br>
<br>
Returns:<br>
ChannelEnd, message<br>
<br>
More detailed usage:<br>
see help(pycsp.AltSelect)<br>
<br>
</pre>
## <pre>InputGuard</pre> ##
<pre>
Help on class InputGuard in module pycsp.parallel.altselect:<br>
<br>
class InputGuard<br>
|  InputGuard(ch_end_read, action=None)<br>
|<br>
|  InputGuard wraps a ChannelEndRead for use with AltSelect/FairSelect.<br>
|<br>
|  If the Inputguard is selected and an action is configured, then the action is executed.<br>
|<br>
|  Usage:<br>
|    >>> ch_end, msg = AltSelect( InputGuard(cin) )<br>
|    >>> ch_end, msg = AltSelect( InputGuard(cin, action="print(channel_input)") )<br>
|    1<br>
|<br>
|    >>> @choice<br>
|    ... def Action(val1, val2, sendResult, channel_input=None):<br>
|    ...     sendResult(channel_input)<br>
|<br>
|    >>> ch_end, msg = AltSelect( InputGuard(cin, action=Action('going into val1', 'going into val2', cout)) )<br>
|<br>
|  InputGuard(ch_end_read, action=None)<br>
|  ch_end_read<br>
|    The ChannelEndRead object to configure as an InputGuard<br>
|  action<br>
|    An action may be provided as a string, a callable function object or a Choice object.<br>
|    The Choice object is the recommended use of action.<br>
|<br>
|    A string:<br>
|      >>> action="L.append(channel_input)"<br>
|<br>
|      The string passed to the action parameter is evaluted in the current namespace and can<br>
|      read variables, but can only write output by editing the content of existing mutable variables.<br>
|      Newly created immutable and mutable variables will only exist in the evalutation of this string.<br>
|<br>
|    callable(func):<br>
|      >>> def func(channel_input=None)<br>
|      ...     L.append(channel_input)<br>
|      >>> action=func<br>
|<br>
|      The callable function object must accept one parameter for actions on InputGuards and must<br>
|      accept zero parameters for actions on OutputGuards.<br>
|<br>
|    Choice:<br>
|      >>> @choice<br>
|      ... def func(L, channel_input=None)<br>
|      ...     L.append(channel_input)<br>
|      >>> action=func(gatherList)<br>
|<br>
|      The choice decorator can be used to make a Choice factory, which can generate actions with<br>
|      different parameters depending on the use case. See help(pycsp.choice)<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __init__(self, ch_end_read, action=None)<br>
<br>
</pre>
## <pre>OutputGuard</pre> ##
<pre>
Help on class OutputGuard in module pycsp.parallel.altselect:<br>
<br>
class OutputGuard<br>
|  OutputGuard(ch_end_write, msg, action=None)<br>
|<br>
|  OutputGuard wraps a ChannelEndWrite for use with AltSelect/FairSelect.<br>
|<br>
|  If the Outputguard is selected and an action is configured, then the action is executed.<br>
|<br>
|  Usage:<br>
|    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=0) )<br>
|    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=1, action="print('done')") )<br>
|    done<br>
|<br>
|    >>> @choice<br>
|    ... def Action(val1, val2):<br>
|    ...     print('%s %s sent' % (val1, val2))<br>
|<br>
|    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=4, action=Action('going into val1', 'going into val2')) )<br>
|    sent<br>
|<br>
|  OutputGuard(ch_end_read, action=None)<br>
|  ch_end_read<br>
|    The ChannelEndWrite object to configure as an OutputGuard<br>
|  msg<br>
|    The message to send. This may be any object for local communication and any object<br>
|    supporting pickling for remote communication.<br>
|  action<br>
|    An action may be provided as a string, a callable function object or a Choice object.<br>
|    The Choice object is the recommended use of action.<br>
|<br>
|    A string:<br>
|      >>> action="L.append(True)"<br>
|<br>
|      The string passed to the action parameter is evaluted in the current namespace and can<br>
|      read variables, but can only write output by editing the content of existing mutable variables.<br>
|      Newly created immutable and mutable variables will only exist in the evalutation of this string.<br>
|<br>
|    callable(func):<br>
|      >>> def func()<br>
|      ...     print("Value sent")<br>
|      >>> action=func<br>
|<br>
|      The callable function object must accept one parameter for actions on InputGuards and must<br>
|      accept zero parameters for actions on OutputGuards.<br>
|<br>
|    Choice:<br>
|      >>> @choice<br>
|      ... def func(L, val)<br>
|      ...     L.remove(val)<br>
|      >>> action=func(gatherList, sending_value)<br>
|<br>
|      The choice decorator can be used to make a Choice factory, which can generate actions with<br>
|      different parameters depending on the use case. See help(pycsp.choice)<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __init__(self, ch_end_write, msg, action=None)<br>
<br>
</pre>
## <pre>SkipGuard</pre> ##
<pre>
Help on class SkipGuard in module pycsp.parallel.guard:<br>
<br>
class SkipGuard(Guard)<br>
|  SkipGuard(action=None)<br>
|<br>
|  SkipGuard will commit a successful communication the moment it is posted.<br>
|<br>
|  Usage:<br>
|    >>> C = Channel()<br>
|    >>> Cin = C.reader()<br>
|    >>> (g, msg) = AltSelect(InputGuard(Cin),  SkipGuard() )<br>
|<br>
|  SkipGuard(action=None)<br>
|  action<br>
|    An action may be provided as a string, a callable function object or a Choice object.<br>
|    The Choice object is the recommended use of action.<br>
|<br>
|    A string:<br>
|      >>> action="L.append(channel_input)"<br>
|<br>
|      The string passed to the action parameter is evaluted in the current namespace and can<br>
|      read variables, but can only write output by editing the content of existing mutable variables.<br>
|      Newly created immutable and mutable variables will only exist in the evalutation of this string.<br>
|<br>
|    callable(func):<br>
|      >>> def func(channel_input=None)<br>
|      ...     L.append(channel_input)<br>
|      >>> action=func<br>
|<br>
|      The callable function object must accept one parameter for actions on InputGuards and must<br>
|      accept zero parameters for actions on OutputGuards.<br>
|<br>
|    Choice:<br>
|      >>> @choice<br>
|      ... def func(L, channel_input=None)<br>
|      ...     L.append(channel_input)<br>
|      >>> action=func(gatherList)<br>
|<br>
|      The choice decorator can be used to make a Choice factory, which can generate actions with<br>
|      different parameters depending on the use case. See help(pycsp.choice)<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __init__(self, action=None)<br>
<br>
</pre>
## <pre>TimeoutGuard</pre> ##
<pre>
Help on class TimeoutGuard in module pycsp.parallel.guard:<br>
<br>
class TimeoutGuard(Guard)<br>
|  TimeoutGuard(seconds, action=None)<br>
|<br>
|  TimeoutGuard spawns a timer thread, when posted. If removed<br>
|  before timeout, then the timer thread is cancelled.<br>
|<br>
|  When the timer expires, the timer thread will commit a successful communication.<br>
|<br>
|  Usage:<br>
|    >>> C = Channel()<br>
|    >>> Cin = C.reader()<br>
|    >>> (g, msg) = AltSelect( InputGuard(Cin), TimeoutGuard(seconds=0.5) )<br>
|<br>
|  TimeoutGuard(action=None)<br>
|  seconds<br>
|    Set the seconds to wait before timeout. eg. 0.5s<br>
|  action<br>
|    An action may be provided as a string, a callable function object or a Choice object.<br>
|    The Choice object is the recommended use of action.<br>
|<br>
|    A string:<br>
|      >>> action="L.append(channel_input)"<br>
|<br>
|      The string passed to the action parameter is evaluted in the current namespace and can<br>
|      read variables, but can only write output by editing the content of existing mutable variables.<br>
|      Newly created immutable and mutable variables will only exist in the evalutation of this string.<br>
|<br>
|    callable(func):<br>
|      >>> def func(channel_input=None)<br>
|      ...     L.append(channel_input)<br>
|      >>> action=func<br>
|<br>
|      The callable function object must accept one parameter for actions on InputGuards and must<br>
|      accept zero parameters for actions on OutputGuards.<br>
|<br>
|    Choice:<br>
|      >>> @choice<br>
|      ... def func(L, channel_input=None)<br>
|      ...     L.append(channel_input)<br>
|      >>> action=func(gatherList)<br>
|<br>
|      The choice decorator can be used to make a Choice factory, which can generate actions with<br>
|      different parameters depending on the use case. See help(pycsp.choice)<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __init__(self, seconds, action=None)<br>
<br>
</pre>
## <pre>@choice</pre> ##
<pre>
Help on function choice in module pycsp.parallel.alternation:<br>
<br>
choice(func)<br>
@choice decorator for making a function into a Choice factory.<br>
<br>
Each generated Choice object can be used as actions in one of<br>
the four guards: InputGuard, OutputGuard, SkipGuard or TimeoutGuard.<br>
<br>
The keyword variable channel_input is special and is provided in the<br>
execution of the choice. Choice functions must accept the channel_input<br>
parameter, when used in InputGuards.<br>
<br>
Usage:<br>
>>> @choice<br>
... def add_service(serviceDB, channel_input):<br>
...     (id, request) = channel_input<br>
...     if serviceDB.has_key(id):<br>
...         serviceDB[id].append(request)<br>
...     else:<br>
...         serviceDB[id] = [request]<br>
<br>
>>> @choice<br>
... def quit(ch_end):<br>
...   poison(ch_end)<br>
<br>
>>> _,_ = AltSelect(<br>
InputGuard(request, action=add_service(services)),<br>
TimeoutGuard(action=quit(request)))<br>
<br>
The Choice factory returned by the @choice decorator:<br>
func(*args, **kwargs)<br>
<br>
</pre>
# <pre>Alternation (alternative to AltSelect)</pre> #
<pre>
Help on class Alternation in module pycsp.parallel.alternation:<br>
<br>
class Alternation<br>
|  Alternation([{cin0:None, (cout0,val):None}])<br>
|<br>
|  Alternation provides the basic interface to Alt. It is recommended<br>
|  to use AltSelect / FairSelect as these are much more user-friendly.<br>
|<br>
|  Alternation supports the SkipGuard, TimeoutGuard, ChannelEndRead<br>
|  or ChannelEndWrite objects.<br>
|<br>
|  Alternation guarantees priority if the flag ensurePriority = True<br>
|<br>
|  Note that alternation always performs the guard that was chosen,<br>
|  i.e. channel input or output is executed within the alternation so<br>
|  even the empty choice with an alternation execution or a choice where<br>
|  the results are simply ignored, still performs the guarded input or<br>
|  output.<br>
|<br>
|  Usage:<br>
|    >>> L = []<br>
|<br>
|    >>> @choice<br>
|    ... def action(channel_input):<br>
|    ...     L.append(channel_input)<br>
|<br>
|    >>> @process<br>
|    ... def P1(cout, n=5):<br>
|    ...     for i in range(n):<br>
|    ...         cout(i)<br>
|<br>
|    >>> @process<br>
|    ... def P2(cin1, cin2, n=10):<br>
|    ...     alt = Alternation([{cin1:action(), cin2:action()}])<br>
|    ...     for i in range(n):<br>
|    ...         alt.execute()<br>
|<br>
|    >>> C1, C2 = Channel(), Channel()<br>
|    >>> Parallel(P1(C1.writer()), P1(C2.writer()), P2(C1.reader(), C2.reader()))<br>
|<br>
|    >>> len(L)<br>
|    10<br>
|<br>
|    >>> L.sort()<br>
|    >>> L<br>
|    [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]<br>
|<br>
|<br>
|    Performing a non-blocking write<br>
|<br>
|    >>> Alternation([<br>
|    ...   { ( cout , datablock ): None } ,  # Try to write to a channel<br>
|    ...   { SkipGuard (): " print('skipped !') } # Skip the alternation<br>
|    ... ]).execute()<br>
|<br>
|    Input with a timeout<br>
|<br>
|    >>> g, msg = Alternation([<br>
|    ...   { cin : None } ,<br>
|    ...   { TimeoutGuard (seconds=1): " print('Ignore this message !') }<br>
|    ... ]).select()<br>
|    >>> if g == cin:<br>
|    ...     print("Got: %s" % (msg))<br>
|<br>
|  Methods defined here:<br>
|<br>
|  __init__(self, guards, ensurePriority=False)<br>
|<br>
|  execute(self)<br>
|      Selects the guard and executes the attached action. Action is a function or python code passed in a string.<br>
|<br>
|      >>> L1,L2 = [],[]<br>
|<br>
|      >>> @process<br>
|      ... def P1(cout, n):<br>
|      ...     for i in range(n):<br>
|      ...         cout(i)<br>
|<br>
|      >>> @process<br>
|      ... def P2(cin1, cin2, n):<br>
|      ...     alt = Alternation([{<br>
|      ...               cin1:"L1.append(channel_input)",<br>
|      ...               cin2:"L2.append(channel_input)"<br>
|      ...           }])<br>
|      ...     for i in range(n):<br>
|      ...         alt.execute()<br>
|<br>
|      >>> C1, C2 = Channel(), Channel()<br>
|      >>> Parallel(P1(C1.writer(),n=10), P1(C2.writer(),n=5), P2(C1.reader(), C2.reader(), n=15))<br>
|<br>
|      >>> len(L1), len(L2)<br>
|      (10, 5)<br>
|<br>
|  select(self)<br>
|      Selects the guard.<br>
|<br>
|      >>> L1,L2 = [],[]<br>
|<br>
|      >>> @process<br>
|      ... def P1(cout, n=5):<br>
|      ...     for i in range(n):<br>
|      ...         cout(i)<br>
|<br>
|      >>> @process<br>
|      ... def P2(cin1, cin2, n=10):<br>
|      ...     alt = Alternation([{<br>
|      ...               cin1:None,<br>
|      ...               cin2:None<br>
|      ...           }])<br>
|      ...     for i in range(n):<br>
|      ...         (g, msg) = alt.select()<br>
|      ...         if g == cin1:<br>
|      ...             L1.append(msg)<br>
|      ...         if g == cin2:<br>
|      ...             L2.append(msg)<br>
|<br>
|      >>> C1, C2 = Channel(), Channel()<br>
|      >>> Parallel(P1(C1.writer()), P1(C2.writer()), P2(C1.reader(), C2.reader()))<br>
|<br>
|      >>> len(L1), len(L2)<br>
|      (5, 5)<br>
<br>
</pre>
# <pre>Termination</pre> #
## <pre>retire</pre> ##
<pre>
Help on function retire in module pycsp.parallel.channel:<br>
<br>
retire(*list_of_channelEnds)<br>
retire(C1, [C2, .. , CN])<br>
<br>
Retire channel ends<br>
<br>
When a channel end is retired, the channel is signaled that a channel end<br>
has now left the channel. When the set of all reading or writing channel ends is set<br>
to none, then the channel enters a retired state whereafter<br>
all actions on the channel will invoke a ChannelRetireException which<br>
is propagated through the PyCSP network to nicely shutdown all processes unless<br>
caugth by the user with a try/except clause.<br>
<br>
Retiring is an improved version of poisoning, which avoids the race condition issue<br>
when terminating multiple concurrent processes.<br>
<br>
Usage:<br>
>>> retire(cin0)<br>
>>> retire(cin0, cin1, cout0)<br>
>>> retire(cinList)<br>
<br>
</pre>
## <pre>poison</pre> ##
<pre>
Help on function poison in module pycsp.parallel.channel:<br>
<br>
poison(*list_of_channelEnds)<br>
poison(C1, [C2, .. , CN])<br>
<br>
Poison channel ends<br>
<br>
When a channel end is poisoned, the channel is set into a poisoned state where<br>
after all actions on the channel will invoke a ChannelPoisonException which<br>
is propagated through the PyCSP network to shutdown all processes unless<br>
caugth by the user with a try/except clause.<br>
<br>
Notice that poisoning may cause race conditions, when terminating multiple concurrent processes.<br>
See retire for an improved shutdown method.<br>
<br>
Usage:<br>
>>> poison(cin0)<br>
>>> poison(cin0, cin1, cout0)<br>
>>> poison(cinList)<br>
<br>
</pre>
## <pre>ChannelRetireException</pre> ##
<pre>
ChannelRetireException()<br>
<br>
Exception thrown by a read or write operation on a channel end.<br>
<br>
In case a ChannelRetireException is raised in a CSP process and not caught, the CSP process<br>
will look for channel ends in the argument list and invoke a retire signal to every found channel end.<br>
<br>
The following network can be shutdown like this:<br>
>>> @process<br>
... def P1(cin, cout):<br>
...     while True:<br>
...         cout(cin()+cin())<br>
<br>
>>> L1, L2, L3 = Channel(), Channel(), Channel()<br>
>>> Parallel(<br>
...   P1(L1.reader(), L2.writer()),<br>
...   P1(L2.reader(), L3.writer())<br>
... )<br>
>>> cout = L1.writer()<br>
<br>
The first P1 process will automatically propagate the signal to the other P1 process<br>
>>> cout.retire()<br>
<br>
Another configuration for process P1 using a custom propagation:<br>
>>> @process<br>
... def P1(cin, cout):<br>
...     try:<br>
...         while True:<br>
...             cout(cin()+cin())<br>
...     except ChannelRetireException:<br>
...         print("Terminating P1")<br>
...         cout.retire()<br>
<br>
</pre>
## <pre>ChannelPoisonException</pre> ##
<pre>
ChannelPoisonException()<br>
<br>
Exception thrown by a read or write operation on a channel end.<br>
<br>
In case a ChannelPoisonException is raised in a CSP process and not caught, the CSP process<br>
will look for channel ends in the argument list and invoke a poison signal to every found channel end.<br>
<br>
The following network can be shutdown like this:<br>
>>> @process<br>
... def P1(cin, cout):<br>
...     while True:<br>
...         cout(cin()+cin())<br>
<br>
>>> L1, L2, L3 = Channel(), Channel(), Channel()<br>
>>> Parallel(<br>
...   P1(L1.reader(), L2.writer()),<br>
...   P1(L2.reader(), L3.writer())<br>
... )<br>
>>> cout = L1.writer()<br>
<br>
The first P1 process will automatically propagate the signal to the other P1 process<br>
>>> cout.poison()<br>
<br>
Another configuration for process P1 using a custom propagation:<br>
>>> @process<br>
... def P1(cin, cout):<br>
...     try:<br>
...         while True:<br>
...             cout(cin()+cin())<br>
...     except ChannelPoisonException:<br>
...         print("Terminating P1")<br>
...         cout.poison()<br>
<br>
</pre>
# <pre>Other</pre> #
## <pre>InfoException</pre> ##
<pre>
InfoException(msg)<br>
<br>
This exception is raised to inform that there is an error in the usage of<br>
PyCSP and also provide a likely solution to fix the error.<br>
<br>
</pre>
## <pre>FatalException</pre> ##
<pre>
FatalException(msg)<br>
<br>
This exception is raised if PyCSP is in an unexpected unstable state, which<br>
is guaranteed to be unrecoverable.<br>
<br>
</pre>
## <pre>current_process_id</pre> ##
<pre>
Help on function current_process_id in module pycsp.parallel.process:<br>
<br>
current_process_id()<br>
Returns the id of the executing CSP process.<br>
<br>
</pre>
## <pre>shutdown</pre> ##
<pre>
Help on function shutdown in module pycsp.parallel.process:<br>
<br>
shutdown()<br>
Closing the PYCSP instance<br>
<br>
Every PyCSP application will create a server thread, to serve incoming communications<br>
on channels. For this reason, it is required to always end the PyCSP application with<br>
a call to shutdown()<br>
<br>
Usage:<br>
>>> shutdown()<br>
<br>
Performs a stable shutdown of hosted channels, waiting for local and remote<br>
processes to disconnect from the hosted channels.<br>
<br>
</pre>