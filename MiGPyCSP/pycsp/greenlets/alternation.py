"""
Alternation module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
  
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Imports
import inspect
import types
from channel import *
from const import *

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
class Choice:
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


class Alternation:
    """
    Alternation supports input and output guards. Guards are ChannelEnd
    or Guard objects.
    
    Note that alternation always performs the guard that was chosen,
    i.e. channel input or output is executed within the alternation so
    even the empty choice with an alternation execution or a choice where
    the results are simply ignored, still performs the guarded input or
    output.
    """
    def __init__(self, guards):
        # Preserve tuple entries and convert dictionary entries to tuple entries
        self.guards = []
        for g in guards:
            if type(g) == types.TupleType:
                self.guards.append(g)
            elif type(g) == types.DictType:
                for elem in g.keys():
                    if type(elem) == types.TupleType:
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

    def set_execute_frame(self, steps):
        if steps > 0:
            self.execute_frame = -1*steps
        else:
            self.execute_frame = steps

    def choose(self):
        reqs={}
        self.s.current.setstate(ACTIVE)
        try:
            idx = 0
            for prio_item in self.guards:
                if len(prio_item) == 3:
                    c, msg, action = prio_item
                    req = ChannelReq(self.s.current, msg=msg)
                    c.post_write(req)
                    op=WRITE
                else:
                    c, action = prio_item
                    req = ChannelReq(self.s.current)
                    c.post_read(req)
                    op=READ
                reqs[req]=(idx, c, op)
                idx += 1

        except (ChannelPoisonException, ChannelRetireException) as e:
            for req in reqs.keys():
                _, c, op = reqs[req]
                if op==READ:
                    c.remove_read(req)
                else:
                    c.remove_write(req)
            raise e

        # If noone have offered a channelrequest, we wait.
        self.s.current.wait()

        act=None
        poison=False
        retire=False
        for req in reqs.keys():
            _, c, op = reqs[req]
            if op==READ:
                c.remove_read(req)
            else:
                c.remove_write(req)            

            if req.result==SUCCESS:
                act=req
            if req.result==POISON:
                poison=True
            if req.result==RETIRE:
                retire=True

        if not act:
            if poison:
                raise ChannelPoisonException()
            if retire:
                raise ChannelRetireException()

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
            elif callable(action):
                # Choice function not allowed as callback
                if type(action) == types.FunctionType and action.func_name == '__choice_fn':
                    raise Exception('@choice function is not instantiated. Please use action() and not just action')
                else:
                    # Execute callback function
                    if op==WRITE:
                        action()
                    else:
                        action(channel_input=req.msg)

            # Compiling and executing string
            elif type(action) == types.StringType:
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

            elif type(action) == types.NoneType:
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


class InputGuard:
    def __init__(self, ch_end, action=None):
        if ch_end.op == READ:
            self.g = (ch_end, action)
        else:
            raise Exception('InputGuard requires an input ch_end')

class OutputGuard:
    def __init__(self, ch_end, msg, action=None):
        if ch_end.op == WRITE:
            self.g = (ch_end, msg, action)
        else:
            raise Exception('OutputGuard requires an output ch_end')

def AltSelect(*guards):
    L = []
    # Build guard list
    for item in guards:
        try:
            L.append(item.g)
        except AttributeError:
            raise Exception('Cannot use ' + str(item) + ' as guard. Only use *Guard types for AltSelect')

    a = Alternation(L)
    a.set_execute_frame(-2)
    return a.execute()


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
