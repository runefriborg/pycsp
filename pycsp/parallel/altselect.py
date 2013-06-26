"""
Adds a better Alt interface.

It includes a priority select and a fair select.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

import inspect

from pycsp.parallel.alternation import Alternation
from pycsp.parallel.process import current_process_id

from pycsp.parallel.const import *
from pycsp.parallel.exceptions import *
import pycsp.current


class InputGuard:
    """ InputGuard(ch_end_read, action=None)

    InputGuard wraps a ChannelEndRead for use with AltSelect/FairSelect.
    
    If the Inputguard is selected and an action is configured, then the action is executed.

    Usage:
      >>> ch_end, msg = AltSelect( InputGuard(cin) )
      >>> ch_end, msg = AltSelect( InputGuard(cin, action="print(channel_input)") )
      1
    
      >>> @choice
      ... def Action(val1, val2, sendResult, channel_input=None):
      ...     sendResult(channel_input)      

      >>> ch_end, msg = AltSelect( InputGuard(cin, action=Action('going into val1', 'going into val2', cout)) )

    InputGuard(ch_end_read, action=None)
    ch_end_read
      The ChannelEndRead object to configure as an InputGuard
    action
      An action may be provided as a string, a callable function object or a Choice object.
      The Choice object is the recommended use of action.
      
      A string:
        >>> action="L.append(channel_input)"
      
        The string passed to the action parameter is evaluted in the current namespace and can 
        read variables, but can only write output by editing the content of existing mutable variables.
        Newly created immutable and mutable variables will only exist in the evalutation of this string.
      
      callable(func):
        >>> def func(channel_input=None)
        ...     L.append(channel_input)
        >>> action=func
        
        The callable function object must accept one parameter for actions on InputGuards and must
        accept zero parameters for actions on OutputGuards.

      Choice:
        >>> @choice
        ... def func(L, channel_input=None)
        ...     L.append(channel_input)
        >>> action=func(gatherList)

        The choice decorator can be used to make a Choice factory, which can generate actions with
        different parameters depending on the use case. See help(pycsp.choice)
    """
    def __init__(self, ch_end_read, action=None):
        try:
            if ch_end_read._op == READ:
                self.g = (ch_end_read, action)
            else:
                raise InfoException('Can not use ChannelEndWrite object. InputGuard requires a ChannelEndRead object')
        except AttributeError:
            raise InfoException('Can not use ' + str(ch_end_read) + ' as ch_end_read. InputGuard requires a ChannelEndRead object')

class OutputGuard:
    """ OutputGuard(ch_end_write, msg, action=None)

    OutputGuard wraps a ChannelEndWrite for use with AltSelect/FairSelect.
    
    If the Outputguard is selected and an action is configured, then the action is executed.

    Usage:
      >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=0) )
      >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=1, action="print('done')") )
      done

      >>> @choice
      ... def Action(val1, val2):
      ...     print('%s %s sent' % (val1, val2))

      >>> ch_end, msg = AltSelect( OutputGuard(cout, msg=4, action=Action('going into val1', 'going into val2')) )
      sent

    OutputGuard(ch_end_read, action=None)
    ch_end_read
      The ChannelEndWrite object to configure as an OutputGuard
    msg
      The message to send. This may be any object for local communication and any object
      supporting pickling for remote communication.
    action
      An action may be provided as a string, a callable function object or a Choice object.
      The Choice object is the recommended use of action.
      
      A string:
        >>> action="L.append(True)"
      
        The string passed to the action parameter is evaluted in the current namespace and can 
        read variables, but can only write output by editing the content of existing mutable variables.
        Newly created immutable and mutable variables will only exist in the evalutation of this string.
      
      callable(func):
        >>> def func()
        ...     print("Value sent")
        >>> action=func
        
        The callable function object must accept one parameter for actions on InputGuards and must
        accept zero parameters for actions on OutputGuards.

      Choice:
        >>> @choice
        ... def func(L, val)
        ...     L.remove(val)
        >>> action=func(gatherList, sending_value)

        The choice decorator can be used to make a Choice factory, which can generate actions with
        different parameters depending on the use case. See help(pycsp.choice)
    """
    def __init__(self, ch_end_write, msg, action=None):
        try:
            if ch_end_write._op == WRITE:
                self.g = (ch_end_write, msg, action)
            else:
                raise InfoException('Can not use ChannelEndRead object. OutputGuard requires a ChannelEndWrite object')
        except AttributeError:
            raise InfoException('Can not use ' + str(ch_end_write) + ' as ch_end_write. OutputGuard requires a ChannelEndWrite object')


def PriSelect(*guards):
    """ PriSelect(G1, [G2, .. ,GN])
    
    PriSelect performs a prioritized choice from a list of guard objects and
    returns a tuple with the selected channel end and the read msg if
    there is one, otherwise None.

    Usage:
      >>> g,msg = PriSelect(InputGuard(cin1), InputGuard(cin2))
      >>> print("Message:%s" % (str(msg)))

    Returns:
      ChannelEnd, message    

    More detailed usage:
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
      ...         _ = PriSelect( InputGuard(cin1, action=action()), InputGuard(cin2, action=action()) )
                
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
            if type(item) == list:
                for item2 in item:
                    L.append(item2.g)
            else:
                L.append(item.g)        
        except AttributeError:
            if type(item)==list:
                raise InfoException('Cannot use ' + str(item2) + ' as guard. Only use *Guard types for PriSelect')
            else:
                raise InfoException('Cannot use ' + str(item) + ' as guard. Only use *Guard types for PriSelect')

    if pycsp.current.trace:
        import pycsp.common.trace as trace
        a = trace.Alternation(L, ensurePriority=True)
        a._set_execute_frame(-3)
    else:
        a = Alternation(L, ensurePriority=True)
        a._set_execute_frame(-2)

    return a.execute()


def AltSelect(*guards):
    """ AltSelect(G1, [G2, .. ,GN])
    
    AltSelect performs a fast choice from a list of guard objects and
    returns a tuple with the selected channel end and the read msg if
    there is one, otherwise None.

    Usage:
      >>> g,msg = AltSelect(InputGuard(cin1), InputGuard(cin2))
      >>> print("Message:%s" % (str(msg)))

    Returns:
      ChannelEnd, message    

    More detailed usage:

      AltSelect supports skip, timeout, input and output guards. Though,
      it is recommended to use the slightly slower PriSelect when using
      skip guards.

      >>> @choice 
      ... def callback(type, channel_input = None):
      ...    print type, channel_input

      >>> A, B = Channel('A'), Channel('B')
      >>> cin, cout = A.reader(), B.writer()
      >>> g1 = InputGuard(cin, action=callback('input'))
      >>> g2 = OutputGuard(cout, msg=[range(10),range(100)], action=callback('output'))
      >>> g3 = TimeoutGuard(seconds=0.1, action=callback('timeout'))
    
      >>> _ = AltSelect(g1, g2, g3)
      timeout None
    

      Note that AltSelect always performs the guard that was chosen,
      i.e. channel input or output is executed within the AltSelect so
      even the empty choice with an AltSelect or where
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
            if type(item) == list:
                for item2 in item:
                    L.append(item2.g)
            else:
                L.append(item.g)        
        except AttributeError:
            if type(item)==list:
                raise InfoException('Cannot use ' + str(item2) + ' as guard. Only use *Guard types for AltSelect')
            else:
                raise InfoException('Cannot use ' + str(item) + ' as guard. Only use *Guard types for AltSelect')

    if pycsp.current.trace:
        import pycsp.common.trace as trace
        a = trace.Alternation(L)
        a._set_execute_frame(-3)
    else:
        a = Alternation(L)
        a._set_execute_frame(-2)

    return a.execute()


def FairSelect(*guards):
    """  FairSelect(G1, [G2, .. ,GN])

    FairSelect sorts the list of guards in order based on the history for
    the chosen guards in this FairSelect.

    Internally it invokes a priority select on the new order of guards.
    
    Timer and Skip guards are always given lowest priority.

    Usage:
      >>> g,msg = FairSelect(InputGuard(cin1), InputGuard(cin2))
      >>> print("Message:%s" % (str(msg)))

    Returns:
      ChannelEnd, message

    More detailed usage:
      see help(pycsp.AltSelect)
    """
    alt_key = str(current_process_id()) + '_' + str(inspect.currentframe().f_back.f_lineno)
    A = AltHistory()
    H = A.get_history(alt_key)

    L = []
    L_last = []

    def add(obj):
        try:
            chan_name = obj.g[0].channel.name
            if chan_name in H:
                L.append((H[chan_name], obj.g))
            else:
                L.append((0, obj.g))
        except AttributeError:
            try:
                L_last.append(obj.g)
            except AttributeError:
                raise InfoException('Can not use ' + str(item) + ' as guard. Only use *Guard types for AltSelect')

    # Add and organise 2 levels
    for item in guards:
        if type(item) == list:
            for item2 in item:
                add(item2)
        else:
            add(item)

    L.sort()
    L = [x[1] for x in L] + L_last

    if pycsp.current.trace:
        import pycsp.common.trace as trace
        a = trace.Alternation(L, ensurePriority=True)
        a._set_execute_frame(-3)
    else:
        a = Alternation(L, ensurePriority=True)
        a._set_execute_frame(-2)

    result =  a.execute()
    try:
        chan_name = result[0].channel.name
        A.update_history(alt_key, chan_name)
    except:
        # Can not record skip og timer guard.
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
        if not alt_key in self.history:
            self.history[alt_key] = {}
        return self.history[alt_key]

    def update_history(self, alt_key, chan_name):
        if not alt_key in self.history:
            self.history[alt_key] = {}

        H = self.history[alt_key]
        if chan_name in H:
            H[chan_name] += 1
        else:
            H[chan_name] = 1

    
