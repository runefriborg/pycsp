"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports

from guard import Skip, SkipGuard, Timeout, TimeoutGuard
from alternation import choice, Alternation
from altselect import FairSelect, AltSelect, InputGuard, OutputGuard
from channel import Channel, close
from channelend import retire, poison
from process import Process, process, Sequence, Parallel, Spawn, current_process_id
from exceptions import ChannelRetireException, ChannelPoisonException, ChannelSocketException, FatalException
from configuration import *
from compat import *
from protocol import shutdown

version = (0,8,0, 'sockets')
