"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *


Configuration().set(SOCKETS_CONNECT_TIMEOUT, 2)
Configuration().set(SOCKETS_BIND_TIMEOUT, 2)
print "test A"
try:
    A = Channel("A", connect=("",8888))
    raise Exception("Failed test")
except ChannelSocketException as e:
    pass


print "test B"
try:
    A = Channel("A", server=("",9999))
except ChannelSocketException as e:
    raise Exception("Failed test")


print "test C"
try:
    B = Channel("B", server=("",9999))
    raise Exception("Failed test")
except ChannelSocketException as e:
    pass



