"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *

import sys, random

random_port = random.randint(9999,19999)

Configuration().set(SOCKETS_CONNECT_TIMEOUT, 2)
Configuration().set(SOCKETS_BIND_TIMEOUT, 2)

# Overwrites environment setting
Configuration().set(PYCSP_PORT, random_port)


sys.stdout.write("test A - ")
try:
    A = Channel("A", connect=("",8888))
    raise Exception("Failed test")
except ChannelSocketException as e:
    sys.stdout.write("OK\n")

sys.stdout.write("test B - ")
try:
    B = Channel("B") # Start server at random_port
    sys.stdout.write("OK\n")
except ChannelSocketException as e:
    raise Exception("Failed test")

close(B)
