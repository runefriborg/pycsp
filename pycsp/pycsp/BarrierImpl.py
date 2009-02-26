#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP Barrier based on the JCSP barrier. 

Copyright (c) 2007 John Markus Bjørndalen, jmb@cs.uit.no.
See LICENSE.txt for licensing details (MIT License). 
"""

from __future__ import with_statement
import threading

class Barrier(object):
    def __init__(self, nEnrolled):
        self.lock = threading.Condition()
        self.reset(nEnrolled)
    def reset(self, nEnrolled):
        with self.lock:
            self.nEnrolled = nEnrolled
            self.countDown = nEnrolled
            if nEnrolled < 0:
                raise "*** Attempth to set a negative nEnrolled on a barrier"
    def sync(self):
        "Synchronize the invoking process on this barrier."
        with self.lock:
            self.countDown -= 1
            if self.countDown > 0:
                self.lock.wait()
            else:
                self.countDown = self.nEnrolled
                self.lock.notifyAll()
    def enroll(self):
        with self.lock:
            self.nEnrolled += 1
            self.countDown += 1
    def resign(self):
        with self.lock:
            self.nEnrolled -= 1
            self.countDown -= 1
            if self.countDown == 0:
                self.countDown = self.nEnrolled
                self.lock.notifyAll()
            elif self.countDown < 0:
                raise "*** A process has resigned on a barrier when no processes were enrolled ***"
        
