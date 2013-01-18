"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *
import time

@io
def wait(seconds):
    time.sleep(seconds)
	
@process
def delay_output(msg, seconds):
    wait(seconds)
    print(str(msg))

Parallel(
    [ delay_output('%d second delay' % (i),i) for i in range(10)]
    )

shutdown()
