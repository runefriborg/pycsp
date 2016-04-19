"""
Alternation module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import inspect
import types
from pycsp.greenlets.channel import *
from pycsp.common.const import *
import collections

# Decorators
def choice(func):
    """
    Decorator for creating choice objets
    """
    # __choice_fn func_name used to identify function in Alternation.execute
    def __choice_fn(*args, **kwargs):
        return Choice(func, *args, **kwargs)
    return __choice_fn

# Classes
class Choice(object):
    """ Choice(func, *args, **kwargs)
    It is recommended to use the @choice decorator, to create Choice instances
    """
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def invoke_on_input(self, channel_input):
        self.kwargs['channel_input'] = channel_input
        self.fn(*self.args, **self.kwargs)
        del self.kwargs['channel_input']

    def invoke_on_output(self):
        self.fn(*self.args, **self.kwargs)


class Alternation(object):
    """
    Alternation supports input and output guards. Guards are ChannelEnd
    or Guard objects.
    
    Note that alternation always performs the guard that was chosen,
    i.e. channel input or output is executed within the alternation so
    even the empty choice with an alternation execution or a choice where
    the results are simply ignored, still performs the guarded input or
    output.
    """
    def __init__(self, guards, ensurePriority=True):
        # Preserve tuple entries and convert dictionary entries to tuple entries
        self.guards = []
        for g in guards:
            if type(g) == tuple:
                self.guards.append(g)
            elif type(g) == dict:
                for elem in list(g.keys()):
                    if type(elem) == tuple:
                        self.guards.append((elem[0], elem[1], g[elem]))
                    else:
                        self.guards.append((elem, g[elem]))

        # The internal representation of guards is a prioritized list
        # of tuples:
        #   input guard: (channel end, action) 
        #   output guard: (channel end, msg, action)

        self.s = Scheduler()

        # Default is to go one up in stackframe.
        self.execute_frame = -1

    def _set_execute_frame(self, steps):
        if steps > 0:
            self.execute_frame = -1*steps
        else:
            self.execute_frame = steps

    def __result(self, reqs):
        act=None
        poison=False
        retire=False
        for req in list(reqs.keys()):
            _, c, op = reqs[req]
            if op==READ:
                c._remove_read(req)
            else:
                c._remove_write(req)
            if req.result==SUCCESS:
                act=req
            if req.result==POISON:
                poison=True
            if req.result==RETIRE:
                retire=True
        return (act, poison, retire)

    def choose(self):
        reqs={}
        act = None
        poison = False
        retire = False

        self.s.current.setstate(ACTIVE)
        try:
            idx = 0
            for prio_item in self.guards:
                if len(prio_item) == 3:
                    c, msg, action = prio_item
                    req = ChannelReq(self.s.current, msg=msg)
                    c._post_write(req)
                    op=WRITE
                else:
                    c, action = prio_item
                    req = ChannelReq(self.s.current)
                    c._post_read(req)
                    op=READ
                reqs[req]=(idx, c, op)
                idx += 1
        except ChannelPoisonException:
            act, poison, retire = self.__result(reqs)
            if not act:
                raise ChannelPoisonException
        except ChannelRetireException:
            act, poison, retire = self.__result(reqs)
            if not act:
                raise ChannelRetireException

        # If noone have offered a channelrequest, we wait.
        if not act:
            self.s.current.wait()

        if not act:
            act, poison, retire = self.__result(reqs)

            if not act:
                if poison:
                    raise ChannelPoisonException()
                if retire:
                    raise ChannelRetireException()

                print('We should not get here in choice!!!')

        idx, c, op = reqs[act]
        return (idx, act, c, op)

    def execute(self):
        """
        Selects the guard and executes the attached action. Action is a function or python code passed in a string.
        """
        idx, req, c, op = self.choose()
        if self.guards[idx]:
            action = self.guards[idx][-1]

            # Executing Choice object method
            if isinstance(action, Choice):
                if op==WRITE:
                    action.invoke_on_output()
                else:
                    action.invoke_on_input(req.msg)

            # Executing callback function object
            elif isinstance(action, collections.Callable):
                # Choice function not allowed as callback
                if type(action) == types.FunctionType and action.__name__ == '__choice_fn':
                    raise Exception('@choice function is not instantiated. Please use action() and not just action')
                else:
                    # Execute callback function
                    if op==WRITE:
                        action()
                    else:
                        action(channel_input=req.msg)

            # Compiling and executing string
            elif type(action) == str:
                # Fetch process frame and namespace
                processframe= inspect.currentframe()
                steps = self.execute_frame
                while (steps < 0):
                    processframe = processframe.f_back
                    steps += 1
                
                # Compile source provided in a string.
                code = compile(action,processframe.f_code.co_filename + ' line ' + str(processframe.f_lineno) + ' in string' ,'exec')
                f_globals = processframe.f_globals
                f_locals = processframe.f_locals
                if op==READ:
                    f_locals.update({'channel_input':req.msg})

                # Execute action
                exec(code, f_globals, f_locals)

            elif type(action) == type(None):
                pass
            else:
                raise Exception('Failed executing action: '+str(action))

        return (c, req.msg)

    def select(self):
        """
        Selects the guard.
        """
        idx, req, c, op = self.choose()
        return (c, req.msg)

