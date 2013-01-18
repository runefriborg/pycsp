"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 

Versions available: parallel, greenlets
Channels can not be used to communicate between versions.

Modules available
> import pycsp.parallel
> import pycsp.greenlets

> import pycsp.common.trace
> import pycsp.common.plugNplay
> import pycsp.common.toolkit
"""

# Import parallel by default to enable "import pycsp"
if not __name__ == '__main__':
    from pycsp.parallel import *
