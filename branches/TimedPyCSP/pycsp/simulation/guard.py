"""
Adds Skip and Timeout guards

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from simulation import Simulation
import pycsp.greenlets.guard 

class Timeout(pycsp.greenlets.Timeout):
    def __init__(self, seconds):
        pycsp.greenlets.Timeout.__init__(self, seconds)
        self.s = Simulation()
        
        
# Run tests
Timeout.__doc__ = pycsp.greenlets.Timeout.__doc__
def testsuite():
  return
testsuite.__doc__ = pycsp.greenlets.Skip.__doc__
if __name__ == '__main__':
    import doctest
    doctest.testmod()
