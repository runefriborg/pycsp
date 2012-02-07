#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from alternation import *
from channel import *
from channelend import *
from process import * 
from guard import *

# Version
version = (0,5,2, '')


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod(__import__("alternation"))
    doctest.testmod(__import__("channel"))
    doctest.testmod(__import__("channelend"))
    doctest.testmod(__import__("process"))
    doctest.testmod(__import__("guard"))
    doctest.testmod()

