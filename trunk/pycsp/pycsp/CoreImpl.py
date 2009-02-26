#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2007 John Markus Bjørndalen, jmb@cs.uit.no.
See LICENSE.txt for licensing details (MIT License). 
"""

from __future__ import with_statement
import time
import threading
import types
import Guards
import Channels
from Guards import *
from Channels import *
import types

def process(func):
    "Decorator for creating process functions"
    def _call(*args, **kwargs):
        return Process(func, *args, **kwargs)
    return _call

class Process(threading.Thread):
    """PyCSP process container. Arguments are: <function>, *args, **kwargs. 
    Checks for and propagates channel poison (see Channels.py)."""
    def __init__(self, fn, *args, **kwargs):
        threading.Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
    def run(self):
        self.retval = None
        try:
            # Store the returned value from the process
            self.retval = self.fn(*self.args, **self.kwargs)
        except ChannelPoisonException, e:
            # look for channels and channel ends
            for ch in [x for x in self.args if isinstance(x, ChannelEnd) or isinstance(x, Channel)]:
                ch.poison()

def Parallel(*processes):
    """Parallel construct. Takes a list of processes (Python threads) which are started.
    The Parallel construct returns when all given processes exit."""
    # run, then sync with them. 
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    # return a list of the return values from the processes
    return [p.retval for p in processes]
            
def Sequence(*processes):
    """Sequence construct. Takes a list of processes (Python threads) which are started.
    The Sequence construct returns when all given processes exit."""
    for p in processes:
        # Call Run directly instead of start() and join() 
        p.run()
    # return a list of the return values from the processes
    return [p.retval for p in processes]
        

def Spawn(process):
    """Spawns off and starts a PyCSP process in the background, for
    independent execution. Returns the started process."""
    process.start()
    return process

# States for the Alternative construct
_ALT_INACTIVE = "inactive"
_ALT_READY    = "ready"
_ALT_ENABLING = "enabling"
_ALT_WAITING  = "waiting"

class Alternative(object):
    """Alternative. Selects from a list of guards."""
    def __init__(self, *guards):
        self.guards = guards
        # set up a reversed guards list (used in _disableGuards...)
        self.rguards = list(guards)  # converts argument tuple to a new list
        self.rguards.reverse()
        self.selected = None
        self._altMonitor = threading.Condition() 
        self._cond = self._altMonitor # for @synchronized
        self.state = _ALT_INACTIVE
        
    @synchronized
    def _enableGuards(self):
        "Enable guards. If any guard currently 'ready', select the first."
        for g in self.guards:
            if g.enable(self):
                # Current guard is ready, so use this immediately (works for priSelect)
                self.selected = g
                self.state = _ALT_READY
                return
        self.selected = None

    @synchronized
    def _disableGuards(self):
        "Disables guards in reverse order from _enableGuards()."
        if self.selected == None:
            for g in self.rguards:
                if g.disable():
                    self.selected = g
        else:
            # TODO: should perhaps check to see whether entire range was visited in "_enableGuards"
            for g in self.rguards:
                g.disable()

    def select(self):
        return self.priSelect()
    
    def priSelect(self):
        # TODO: Check why we need to do this outside the lock. Condition is an RLock, so we _can_ be recursive.
        # otoh, we could remove the @synchronized for _enableGuards as well. 
        # First, enable guards. 
        self.state = _ALT_ENABLING
        self._enableGuards()
        with self._altMonitor:
            if self.state == _ALT_ENABLING:
                # No guard has been selected yet. Equivalent with self.selected == None. 
                # Wait for one of the guards to become "ready".
                # The guards wake us up by calling schedule() on the alt (see One2OneChannel)
                self.state = _ALT_WAITING
                self._altMonitor.wait()
                self.state = _ALT_READY   # assume we have selected one when woken up
        self._disableGuards()
        self.state = _ALT_INACTIVE
        return self.selected
    
    @synchronized
    def schedule(self):
        """A wake-up call to processes ALTing on guards controlled by this object.
        Called by the guard."""
        if self.state == _ALT_ENABLING:
            # NB/TODO: why allow this? it complicates matters and is hardly likely to help much.
            # must be easier to use the same RLock around most of priSelect (as indicated in the function).
            # in that case, this should never happen since we keep the lock, and a guard should not
            # be allowed to release that lock in the enable() function..... 
            self.state = _ALT_READY
        elif self.state == _ALT_WAITING:
            self.state = _ALT_READY
            self._altMonitor.notify()
