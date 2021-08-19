
This PyCSP implementation has been <b>discontinued</b>.

Go to https://pycsp.github.io/ for other more recent implementations.

<hr>




PyCSP was a CSP library for Python that implemented core CSP
functionality with some extensions from pi-calculus.

Provided:

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

See https://github.com/runefriborg/pycsp/wiki for more information.
