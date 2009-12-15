"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import pycsp.greenlets.channel
from simulation import Simulation

class Channel(pycsp.greenlets.Channel):
    def __init__(self, name=None):
        pycsp.greenlets.Channel.__init__(self,name)
        self.s = Simulation()

# Run tests
Channel.__doc__ = pycsp.greenlets.Channel.__doc__
def testsuite():
  return
from pycsp.greenlets.channelend import *
testsuite.__doc__ = pycsp.greenlets.IN.__doc__
testsuite.__doc__ += '\n'  
testsuite.__doc__ += pycsp.greenlets.OUT.__doc__
testsuite.__doc__ += '\n'  
testsuite.__doc__ += pycsp.greenlets.retire.__doc__
testsuite.__doc__ += '\n'  
testsuite.__doc__ += pycsp.greenlets.poison.__doc__

if __name__ == '__main__':
    import doctest
    doctest.testmod()
