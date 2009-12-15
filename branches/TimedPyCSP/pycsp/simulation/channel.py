"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from pycsp.greenlets.channel import Channel as gChannel
from simulation import Simulation

class Channel(gChannel):
    def __init__(self, name=None):
        gChannel.__init__(self,name)
        self.s = Simulation()

# Run tests
Channel.__doc__ = gChannel.__doc__
if __name__ == '__main__':
    import doctest
    doctest.testmod()
