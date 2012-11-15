"""
Constructs added to allow easy switching between PyCSP implementations.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""
from exceptions import *

def shutdown():
    """
    Perform shutdown of non-active hosted channels. Wait
    for active hosted channels to become non-active.
    """
    return


def multiprocess(func=None, port=None):
    raise InfoException("multiprocess not available for greenlets")


class MultiProcess():
    def __init__(self, fn, port, *args, **kwargs):
        raise InfoException("MultiProcess not available for greenlets")

class ChannelSocketException(Exception):
    def __init__(self, addr, msg):
        self.msg = msg
        self.addr = addr
    def __str__(self):
        return repr("%s %s" % (self.msg, self.addr))

