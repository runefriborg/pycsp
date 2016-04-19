"""
Adds a better Alt interface.

It includes a priority select and a fair select.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp.greenlets.alternation import Alternation
from pycsp.greenlets.process import current_process_id

from pycsp.common.const import *
import pycsp.current

import inspect

class InputGuard(object):
    """
    InputGuard wraps an input ch_end for use with AltSelect.

    >>> from __init__ import *

    >>> C = Channel()
    >>> cin, cout = C.reader(), C.writer()

    >>> @process
    ... def P1(cout):
    ...     for i in range(3): cout(i)

    >>> Spawn (P1(cout))

    >>> ch_end, msg = AltSelect( InputGuard(cin) )
    >>> ch_end, msg = AltSelect( InputGuard(cin, action="print channel_input") )
    1
    >>> ch_end, msg = AltSelect( InputGuard(cin, action=lambda channel_input: Spawn(Process(cout, channel_input))) )
    
    >>> @choice
    ... def Action(val1, val2, channel_input=None):
    ...     print channel_input

    >>> ch_end, msg = AltSelect( InputGuard(cin, action=Action('going into val1', 'going into val2')) )
    2
    """
    def __init__(self, ch_end, action=None):
        try:
            if ch_end._op == READ:
                self.g = (ch_end, action)
            else:
                raise Exception('InputGuard requires an input ch_end')
        except AttributeError:
            raise Exception('Cannot use ' + str(ch_end) + ' as input ch_end')

class OutputGuard(object):
    """
    OutputGuard wraps an output ch_end for use with AltSelect.

    >>> from __init__ import *

    >>> C = Channel()
    >>> cin, cout = C.reader(), C.writer()

    >>> @process
    ... def P1(cin):
    ...     for i in range(5): cin()

    >>> Spawn (P1(cin))

    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=0) )
    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=1, action="print 'done'") )
    done

    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=2, action=lambda: Spawn(Process(cout, 3))) )
    
    >>> @choice
    ... def Action(val1, val2):
    ...     print 'sent'

    >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=4, action=Action('going into val1', 'going into val2')) )
    sent
    """
    def __init__(self, ch_end, msg, action=None):
        try:
            if ch_end._op == WRITE:
                self.g = (ch_end, msg, action)
            else:
                raise Exception('OutputGuard requires an output ch_end')
        except AttributeError:
            raise Exception('Cannot use ' + str(ch_end) + ' as output ch_end')


def PriSelect(*guards):
    """
    PriSelect is a wrapper to Alternation with a much more intuitive
    interface. 
    It performs a prioritized choice from a list of guard objects and
    returns a tuple with the selected channel end and the read msg if
    there is one, otherwise None.

    >>> from __init__ import *

    >>> C = Channel()
    >>> cin = C.reader()

    >>> ch_end, msg = PriSelect(InputGuard(cin), SkipGuard())

    >>> if ch_end == cin:
    ...     print msg
    ... else:
    ...     print msg == None
    True


    PriSelect supports skip, timeout, input and output guards.

    >>> @choice 
    ... def callback(type, channel_input = None):
    ...    print type, channel_input

    >>> A, B = Channel('A'), Channel('B')
    >>> cin, cout = A.reader(), B.writer()
    >>> g1 = InputGuard(cin, action=callback('input'))
    >>> g2 = OutputGuard(cout, msg=[range(10),range(100)], action=callback('output'))
    >>> g3 = TimeoutGuard(seconds=0.1, action=callback('timeout'))
    
    >>> _ = PriSelect(g1, g2, g3)
    timeout None
    

    Note that PriSelect always performs the guard that was chosen,
    i.e. channel input or output is executed within the PriSelect so
    even the empty choice with an PriSelect or where
    the results are simply ignored, still performs the guarded input or
    output.

    >>> L = []

    >>> @choice 
    ... def action(channel_input):
    ...     L.append(channel_input)

    >>> @process
    ... def P1(cout, n=5):
    ...     for i in range(n):
    ...         cout(i)
    
    >>> @process
    ... def P2(cin1, cin2, n=10):
    ...     for i in range(n):
    ...         _ = AltSelect( InputGuard(cin1, action=action()), InputGuard(cin2, action=action()) )
                
    >>> C1, C2 = Channel(), Channel()
    >>> Parallel(P1(C1.writer()), P1(C2.writer()), P2(C1.reader(), C2.reader()))

    >>> len(L)
    10

    >>> L.sort()
    >>> L
    [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
    """
    L = []
    # Build guard list
    for item in guards:
        try:
            L.append(item.g)
        except AttributeError:
            raise Exception('Cannot use ' + str(item) + ' as guard. Only use *Guard types for Pri/AltSelect')

    if pycsp.current.trace:
        import pycsp.common.trace as trace
        a = trace.Alternation(L)
        a._set_execute_frame(-3)
    else:
        a = Alternation(L)
        a._set_execute_frame(-2)

    return a.execute()

AltSelect = PriSelect

def FairSelect(*guards):
    """ 
    It sorts the list of guards in order based on the history for
    the chosen guards in this FairSelect located at a specific line in a specific process.

    Internally it invokes a priority select on the new order of guards.
    
    Timer and Skip guards are placed with lowest priority, since it does make sence to make them
    fair.
    """
    alt_key = str(current_process_id()) + '_' + str(inspect.currentframe().f_back.f_lineno)
    A = AltHistory()
    H = A.get_history(alt_key)

    L = []
    L_last = []
    for item in guards:
        try:
            chan_name = item.g[0].channel.name
            if chan_name in H:
                L.append((H[chan_name], item.g))
            else:
                L.append((0, item.g))
        except AttributeError:
            try:
                L_last.append(item.g)
            except AttributeError:
                raise Exception('Can not use ' + str(item) + ' as guard. Only use *Guard types for AltSelect')
    L.sort()
    L = [x[1] for x in L] + L_last

    if pycsp.current.trace:
        import pycsp.common.trace as trace
        a = trace.Alternation(L)
        a._set_execute_frame(-3)
    else:
        a = Alternation(L)
        a._set_execute_frame(-2)

    result =  a.execute()
    try:
        chan_name = result[0].channel.name
        A.update_history(alt_key, chan_name)
    except:
        # Can not record skip or timer guard.
        pass
    return result


class AltHistory(object):
    """ A special singleton class
    
    It records the history of Fair Selects, based on an alt_key unique for every
    location in the source code.    
    """
    __instance = None  # the unique instance
    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)
        
    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:
            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)

            # Create history container
            # key = (process_id, line number)
            # value = {chan.name:selects}
            cls.__instance.history = {}
        return cls.__instance
    getInstance = classmethod(getInstance)

    def get_history(self, alt_key):
        if alt_key not in self.history:
            self.history[alt_key] = {}
        return self.history[alt_key]

    def update_history(self, alt_key, chan_name):
        if alt_key not in self.history:
            self.history[alt_key] = {}

        H = self.history[alt_key]
        if chan_name in H:
            H[chan_name] += 1
        else:
            H[chan_name] = 1

    
