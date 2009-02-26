#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
CSP Guards for PyCSP.

Copyright (c) 2007 John Markus Bjørndalen, jmb@cs.uit.no.
See LICENSE.txt for licensing details (MIT License).
"""

import time
import threading

class Guard(object):
    # JCSPSRC/src/com/quickstone/jcsp/lang/Guard.java
    def enable(self, alt):
        return False
    def disable(self):
        return False

class Skip(Guard):
    # JCSPSRC/src/com/quickstone/jcsp/lang/Skip.java
    def enable(self, alt):
        #Thread.yield() in java version
        return True
    def disable(self):
        return True

# class CSTimer(Guard):
# TODO: may need a process to do this? 

# TODO: Robert
# Spawns a separate timer thread. How does that affect poison etc? Any problems?
# Might want to create a process to properly catch poison. 
class Timer(Guard):
    def __init__(self, seconds):
        self.expired = False
        self.timer = threading.Timer(seconds, self.expire)
        self.alt = None

    def enable(self, alt):
        self.alt = alt
        self.timer.start()
        return False

    def disable(self):
        self.timer.cancel()
        self.alt = None
        return self.expired
        
    def expire(self):
        self.expired = True
        self.alt.schedule()
        
