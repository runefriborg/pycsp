The PyCSP project is an on-going project to bring CSP (Communicating Sequential Processes) to Python.

It was started in 2006 and is still under active development.
Bug reports and suggestions for new features are most welcome.

# News #
( Updated 2013-02-14 )
Released PyCSP 0.9.0

( Updated 2013-02-13 )
Found a design flaw in AltSelect, which means that AltSelect does not guarantee priority when affected by network and scheduling latencies. A new PriSelect have been added which is slightly slower but does guarantee priority and thus should be used whenever the SkipGuard is needed.

( Updated 2013-01-21 )
Windows support has now been tested and should work, with a few differences when using @multiprocess. Getting closer to a release. Still a few minor tweaks and bugs left. Please use the latest version from svn. See below for instructions.

( Updated 2012-12-13 )
We are finally very close to releasing a new 0.9.0 version, which will provide a long list of new features. The project is considered stable on linux or MacOSX and we recommend that downloads are retrieved by fetching the latest trunk version using svn. Currently windows is not supported. We recommend using CPython 2.7.

The documentation on this website is updated to focus on the 0.9.0 PyCSP version.

```
wget http://pycsp.googlecode.com/files/pycsp-complete-0.9.0.tar.gz
tar -zxf pycsp-complete-0.9.0.tar.gz
cd pycsp-0.9.0
sudo python setup.py install
```

# PyCSP Provides #

  * A flexible CSP library for Python
  * Synchronous communication
  * Buffered channels
  * Multiple process types such as, greenlets, threads, processes and remote processes
  * Both input and output guards supported in external choice (Alts)
  * A single any-to-any channel type
  * Mobile channel-ends
  * Retire and poison signals for shutting down networks nicely
  * A channel which can communicate using inter-process communication as well as sockets.
  * A PyCSP providing local and distributed communication using only standard python modules bundled with CPython
  * NAT traversal
  * Tracing PyCSP executions to a log file, for later visualisation

# Project Plan #
  * Add visualisation of tracing information for hosts, when using distributed communication
  * Add Python3 support
  * Add ssh\_process, qsub\_process (PBS) and grid\_process process types

# Getting Started #

The best way to get started on PyCSP is through the tutorials:

  * [First Glimpse](Getting_Started_With_PyCSP.md)
    * [Installation and Basics](Getting_Started_With_PyCSP.md)
    * [Buffering and External Choice](Getting_Started_With_PyCSP_2.md)
    * [Controlling Termination](Getting_Started_With_PyCSP_3.md)
    * [A Scalable Webserver](Getting_Started_With_PyCSP_4.md)
  * [Various Process Types](Getting_Started_With_Other_Processes.md)
  * [The Trace Module](Getting_Started_With_Tracing.md)
  * [Distributed Channels](Getting_Started_With_Parallel.md)
  * [Some Syntactic Sugar](Getting_Started_With_Syntactic_Sugar.md)

Documentation on all parts of PyCSP: [Reference documentation](PyCSP_0_9_0_Reference.md)

Example:

<img src='http://pycsp.googlecode.com/files/animate_sink.gif' align='right' width='300' height='300'>

<pre><code>import sys<br>
from pycsp.parallel import *<br>
<br>
@process<br>
def source(chan_out):<br>
    for i in range(10):<br>
        chan_out("Hello world (%d)\n" % (i))<br>
    retire(chan_out)<br>
    <br>
@process<br>
def sink(chan_in):<br>
    while True:<br>
        sys.stdout.write(chan_in())<br>
<br>
chan = Channel()<br>
Parallel(<br>
    5 * source(-chan),<br>
    5 * sink(+chan)<br>
)<br>
<br>
shutdown()<br>
</code></pre>


<h1>Related publications</h1>

<ul><li>Friborg, Rune Møllegaard ; Vinter, Brian. <i><a href='http://www.wotug.org/papers/CPA-2011/FriborgVinter11/FriborgVinter11.pdf'>Verification of a Dynamic Channel Model using the SPIN Model Checker</a></i>. Communicating Process Architectures 2011 : WoTUG-33, Proceedings of the 33st WoTUG Technical Meeting (CPA-11). Limerick, Ireland.</li></ul>

<ul><li>Friborg, Rune Møllegaard ; Vinter, Brian. <i><a href='http://dx.doi.org/10.1016/j.jocs.2011.02.001'>Rapid development of scalable scientific software using a process oriented approach</a></i>. Journal of Computational Science</li></ul>

<ul><li>Friborg, Rune Møllegaard ; Vinter, Brian ; Bjørndalen, John Markus. <i><a href='http://www.humanpub.org/ijipm/ppl/7-IJIPM1-054050.pdf'>PyCSP - controlled concurrency</a></i>. International Journal of Information Processing and Management, Volume 1, Number 2, October 2010</li></ul>

<ul><li>Vinter, Brian ; Bjørndalen, John Markus ; Friborg, Rune Møllegaard. <i><a href='http://www.wotug.org/papers/CPA-2009/Vinter09/Vinter09.pdf'>PyCSP Revisited</a></i>. Communicating Process Architectures 2009 : WoTUG-32, Proceedings of the 32st WoTUG Technical Meeting (CPA-09). Eindhoven, The Netherlands.</li></ul>

<ul><li>Friborg, Rune Møllegaard ; Bjørndalen, John Markus ; Vinter, Brian. <i><a href='http://www.wotug.org/papers/CPA-2009/Friborg09/Friborg09.pdf'>Three Unique Implementations of Processes for PyCSP</a></i>. Communicating Process Architectures 2009 : WoTUG-32, Proceedings of the 32st WoTUG Technical Meeting (CPA-09). Eindhoven, The Netherlands.</li></ul>

<ul><li>Friborg, Rune Møllegaard ; Vinter, Brian. <i><a href='http://www.wotug.org/paperdb/send_file.php?num=241'>CSPBuilder - CSP based Scientific Workflow Modelling</a></i>. Communicating Process Architectures 2008 : WoTUG-31, Proceedings of the 31st WoTUG Technical Meeting (CPA-08). York, UK.</li></ul>

<ul><li>Bjørndalen, John Markus ; Sampson, Adam T. <i><a href='http://www.cs.uit.no/~johnm/publications/pdf/bjorndalen2008process-oriented.pdf'>Process-Oriented Collective Operations</a></i>. Communicating Process Architectures 2008 : WoTUG-31, Proceedings of the 31st WoTUG Technical Meeting (CPA-08). York, UK.</li></ul>

<ul><li>Bjørndalen, John Markus ; Vinter, Brian ; Anshus, Otto. <i><a href='http://www.wotug.org/paperdb/send_file.php?num=216'>PyCSP - Communicating Sequential Processes for Python</a></i>. Communicating Process Architectures 2007 : WoTUG-30, Proceedings of the 30st WoTUG Technical Meeting (CPA-07). Surrey, UK.