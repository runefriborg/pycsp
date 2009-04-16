#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjørndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

version = (0,5,1)

from alternation import *
from channel import *
from channelend import *
from process import * 
from guard import *
