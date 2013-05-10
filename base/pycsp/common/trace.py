"""
Trace module

Trace functions:
  TraceInit(<filename or file object>)
  TraceMsg(<message>)
  TraceQuit()

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

import sys
import pycsp.current as pycsp
from pycsp.current import *

# Import toolkit process for writing to a file.
from pycsp.common import toolkit as pycsp_toolkit

# Set trace mode
pycsp.trace = True

# Setup gather system
C = [pycsp.Channel('TraceChan_A'), pycsp.Channel('TraceChan_B')]

@pycsp.process
def Convert2Str(cin, cout):
    while True:
        cout(str(cin()) + '\n')

def sendTrace(msg):
    cout = C[0].writer()
    cout(msg)
    pycsp.retire(cout)

        
def TraceInit(file=None, stdout=False):
    """  TraceInit(<filename or file object>, <trace stdout>)
    Spawn the collecting trace process.
    Only run once, otherwise multiple trace files is created.

    This function must be called before tracing.
    """

    class PipeHandler:
        def __init__(self, wrapped_pipe):
            self.wrapped_pipe = wrapped_pipe
        def write(self, s):
            sendTrace({'type':'Output', 'msg':s})
            self.wrapped_pipe.write(s)
        def flush(self):
            self.wrapped_pipe.flush()

    if stdout:
        sys.stdout = PipeHandler(sys.stdout)
    
    if file == None:
        file = 'pycsp_trace.log'


    pycsp.Spawn(Convert2Str(C[0].reader(), C[1].writer()),
                pycsp_toolkit.file_w(C[1].reader(), file)) 


_TraceQuit = C[0].writer().retire

def TraceQuit():
    """ TraceQuit()
    Shutdown collecting trace process, by retiring the
    connected channelend.

    Application will hang if this is not invoked.
    
    This function will abort tracing when called.
    """
    sendTrace({'type':'TraceQuit'})
    _TraceQuit()


def TraceMsg(s):
    """ TraceMsg(<message>)
    Will add the trace message to the log:
      {'type':'Msg', 'msg':<message>}
    
    """
    sendTrace({'type':'Msg', 'process_id':pycsp.current_process_id(), 'msg':str(s)})


# Overwriting all necessary functions / classes to add tracing. Tracing
# is done by writing to the C[0] channel through sendTrace(msg). A
# trace msg is a python dictionary with the 'type' hash key defining the
# trace type.
# 
# The following trace types are performed: Channel, ChannelEndRead, StartProcess,
#   QuitProcess, BlockOnParallel, DoneParallel, BlockOnSequence, DoneSequence,
#   Spawn, Poison, BlockOnWrite, DoneWrite, BlockOnRead, DoneRead, Alternation,
#   BlockOnAlternation.select, DoneAlternation.select, BlockOnAlternation.execute,
#   DoneAlternation.execute

from pycsp.common.const import *

def process(func):
    def _call(*args, **kwargs):
        def wrapfunc(*wrap_args, **wrap_kwargs):
            process_id = pycsp.current_process_id()
            sendTrace({'type':'StartProcess', 'func_name':func.func_name, 'process_id':process_id})
            try:
                func(*wrap_args, **wrap_kwargs)
            finally:
                sendTrace({'type':'QuitProcess', 'func_name':func.func_name, 'process_id':process_id})
        wrapfunc.func_name = func.func_name
        t = pycsp.Process(wrapfunc, *args, **kwargs)
        return t
    return _call

def Parallel(*plist):
    process_id = pycsp.current_process_id()
    val = {'processes':[], 'process_id':process_id}
    for p in plist:
        if type(p) == type([]):            
            for p_2 in p:
                val['processes'].append({'func_name':p_2.fn.func_name, 'process_id':p_2.id})
        else:
            val['processes'].append({'func_name':p.fn.func_name, 'process_id':p.id})
    
    val['type'] = 'BlockOnParallel'
    sendTrace(val)
    result = pycsp.Parallel(*plist)
    val['type'] = 'DoneParallel'
    sendTrace(val)
    return result

def Sequence(*plist):
    process_id = pycsp.current_process_id()
    val = {'processes':[], 'process_id':process_id}
    for p in plist:
        if type(p) == type([]):            
            for p_2 in p:
                val['processes'].append({'func_name':p_2.fn.func_name, 'process_id':p_2.id})
        else:
            val['processes'].append({'func_name':p.fn.func_name, 'process_id':p.id})
    val['type'] = 'BlockOnSequence'
    sendTrace(val)
    result = pycsp.Sequence(*plist)
    val['type'] = 'DoneSequence'
    sendTrace(val)
    return result

def Spawn(*plist):
    process_id = pycsp.current_process_id()
    val = {'type':'Spawn', 'processes':[], 'process_id':process_id}
    for p in plist:
        if type(p) == type([]):
            for p_2 in p:
                val['processes'].append({'func_name':p_2.fn.func_name, 'process_id':p_2.id})
        else:
            val['processes'].append({'func_name':p.fn.func_name, 'process_id':p.id})
    sendTrace(val)
    pycsp.Spawn(*plist)



class ChannelEndReadTrace:
    def __init__(self, wrapped, chan):
        self.wrapped = wrapped

        self.channel = chan
        self._op = READ

        self._post_read = self.wrapped._post_read
        self._remove_read = self.wrapped._remove_read
        self.__repr__ = self.wrapped.__repr__
        self.isWriter = self.wrapped.isWriter
        self.isReader = self.wrapped.isReader

        self.count = 0

    def retire(self): 
        process_id = pycsp.current_process_id()
        sendTrace({'type':'Retire', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
        self.wrapped.retire()       

    def poison(self): 
        process_id = pycsp.current_process_id()
        sendTrace({'type':'Poison', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
        self.wrapped.poison()       

    def __call__(self):
        process_id = pycsp.current_process_id()
        sendTrace({'type':'BlockOnRead', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
        msg = self.wrapped.__call__()
        sendTrace({'type':'DoneRead', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
        self.count += 1
        return msg


class ChannelEndWriteTrace:
    def __init__(self, wrapped, chan):
        self.wrapped = wrapped

        self.channel = chan
        self._op = WRITE

        self._post_write = self.wrapped._post_write
        self._remove_write = self.wrapped._remove_write
        self.__repr__ = self.wrapped.__repr__
        self.isWriter = self.wrapped.isWriter
        self.isReader = self.wrapped.isReader
        self.count = 0

    def retire(self): 
        process_id = pycsp.current_process_id()
        sendTrace({'type':'Retire', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
        self.wrapped.retire()       

    def poison(self): 
        process_id = pycsp.current_process_id()
        sendTrace({'type':'Poison', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
        self.wrapped.poison()       

    def __call__(self, msg):
        process_id = pycsp.current_process_id()
        sendTrace({'type':'BlockOnWrite', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
        self.wrapped.__call__(msg)
        sendTrace({'type':'DoneWrite', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
        
#        try:
#            sendTrace({'type':'BlockOnWrite', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
#            self.wrapped.__call__(msg)
#            sendTrace({'type':'DoneWrite', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
#        except pycsp.ChannelRetireException:
#            sendTrace({'type':'PoisonWrite', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
#            raise pycsp.ChannelRetireException
#        except pycsp.ChannelPoisonException:
#            sendTrace({'type':'RetireWrite', 'id':self.count, 'chan_name':self.wrapped.channel.name, 'process_id':process_id})
#            raise pycsp.ChannelPoisonException

        self.count += 1

class Alternation:
    def __init__(self, guards, ensurePriority=False):
        self.wrapped = pycsp.Alternation(guards, ensurePriority=ensurePriority)
        self.wrapped._set_execute_frame(-2)
        self._set_execute_frame = self.wrapped._set_execute_frame

        process_id = pycsp.current_process_id()
        val = {'type':'Alternation', 'guards':[], 'process_id':process_id}
        for g_tuple in self.wrapped.guards:
            val['guards'].append(self.__translate(g_tuple[0]))
        sendTrace(val)

    def __translate(self, g):        
        if isinstance(g, TimeoutGuard):
            return {'type':'TimeoutGuard'}
        elif isinstance(g, SkipGuard):
            return {'type':'SkipGuard'}
        elif isinstance(g, ChannelEndReadTrace):
            return {'type':'ReadGuard', 'chan_name':g.wrapped.channel.name}
        elif isinstance(g, ChannelEndWriteTrace):
            return {'type':'WriteGuard', 'chan_name':g.wrapped.channel.name}

    def select(self):
        process_id = pycsp.current_process_id()
        sendTrace({'type':'BlockOnAlternation.select', 'process_id':process_id})
        result = self.wrapped.select()
        sendTrace({'type':'DoneAlternation.select', 'guard':self.__translate(result[0]), 'process_id':process_id})
        return result

    def execute(self):
        process_id = pycsp.current_process_id()
        sendTrace({'type':'BlockOnAlternation.execute', 'process_id':process_id})
        result = self.wrapped.execute()
        sendTrace({'type':'DoneAlternation.execute', 'guard':self.__translate(result[0]), 'process_id':process_id})
        return result
        

class Channel:
    def __init__(self, *args, **kwargs):
        self.wrapped = pycsp.Channel(*args, **kwargs)
        self.name = self.wrapped.name
        sendTrace({'type':'Channel', 'chan_name':self.wrapped.name})

    def poison(self):
        sendTrace({'type':'Poison', 'chan_name':self.wrapped.name})
        self.wrapped.poison()

    # syntactic sugar: cin = +chan
    def __pos__(self):
        return self.reader()
    
    # syntactic sugar: cout = -chan
    def __neg__(self):
        return self.writer()

    # syntactic sugar: Channel() * N
    def __mul__(self, multiplier):
        new = [self]
        for i in range(multiplier-1):
            new.append(Channel(name=self.name+str(i+1)))
        return new

    # syntactic sugar: N * Channel()
    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)

    def reader(self):
        ch_end = self.wrapped.reader()
        sendTrace({'type':'ChannelEndRead', 'chan_name':self.wrapped.name})
        return ChannelEndReadTrace(ch_end, self)

    def writer(self):
        ch_end = self.wrapped.writer()
        sendTrace({'type':'ChannelEndWrite', 'chan_name':self.wrapped.name})
        return ChannelEndWriteTrace(ch_end, self)
