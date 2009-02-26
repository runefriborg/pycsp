#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2007 John Markus Bjørndalen, jmb@cs.uit.no.
See LICENSE.txt for licensing details (MIT License). 
"""

from __future__ import with_statement
from Guards import *
from Channels import *
from BarrierImpl import Barrier
from CoreImpl import * 
