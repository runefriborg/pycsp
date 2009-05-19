"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import threading
import uuid
import Pyro.naming, Pyro.core

from configuration import *
from alternation import *
from channel import *
from guard import *

# Constants
ACTIVE, DONE, POISON = range(3)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

# Classes
class PyroServerProcess(threading.Thread):
    def __init__(self, ns):
        threading.Thread.__init__(self)
        self.ns = ns
        self.managerObj = None
        self.cond = threading.Condition()

    def run(self):
        self.cond.acquire()
        Pyro.core.initServer()
        Pyro.config.PYRO_NS_DEFAULTGROUP=':PyCSP'

        # make sure our namespace group exists
        try:
            self.ns.createGroup(':PyCSP')
        except Pyro.errors.NamingError:
            pass

        daemon = Pyro.core.Daemon()
        daemon.useNameServer(self.ns)
        self.managerObj = PyroServerManager()
        daemon.connectPersistent(self.managerObj, 'SERVER-'+str(Configuration().get(NET_SERVER_ID)))
        self.cond.notify()
        self.cond.release()
        
        #Starting requestLoop'
        
        try:
            daemon.requestLoop()
        except Exception, e:
            daemon.disconnect(self.managerObj)
            daemon.shutdown()
            raise Exception(e)
        

class PyroServerManager(Pyro.core.ObjBase):
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
        self.ChannelIndex = {}
        self.AlternationIndex = {}
        self.lock = threading.RLock()

    def Alternation(self, reduced_guards):
        self.lock.acquire()
        id = str(uuid.uuid1())

        # Swap channelends for channels, preserve guards
        new_guards = []
        for D in reduced_guards:
            new_D = {}
            for c in D.keys():
                (op, msg) = D[c]

                if not isinstance(c, Guard):
                    # Swap channelend for channel
                    if not self.ChannelIndex.has_key(c):
                        self.lock.release()
                        raise ChannelPoisonException()

                    c = self.ChannelIndex[c]

                if op == READ:
                    new_D[c] = None
                else:
                    new_D[(c,msg)] = None
            new_guards.append(new_D)

        self.AlternationIndex[id] = RealAlternation(new_guards)
        self.lock.release()
        return id

    def Alternation_delete(self, id):
        del self.AlternationIndex[id]


    def Alternation_choose(self, id):
        pri_idx, act, c, req, op = self.AlternationIndex[id].choose()
        if isinstance(c, RealChannel):
            c = c.name
        return pri_idx, c, req.msg, op

    def Channel(self, name = None):
        self.lock.acquire()
        id = name
        if id == None:
            c = RealChannel()
            self.ChannelIndex[c.name] = c
            id = c.name
        elif not self.ChannelIndex.has_key(id):
            self.ChannelIndex[id] = RealChannel(id)
        self.lock.release()
        return id

    def Channel_delete(self, id):
        del self.ChannelIndex[id]
        
    def Channel_read(self, id):
        try:
            return self.ChannelIndex[id]._read()
        except KeyError:
            raise ChannelPoisonException()

    def Channel_write(self, id, msg):
        try:
            return self.ChannelIndex[id]._write(msg)
        except KeyError:
            raise ChannelPoisonException()

    def Channel_poison(self, id):
        try:
            self.ChannelIndex[id].poison()
            self.Channel_delete(id)
        except KeyError:
            pass
        
    def Channel_join_reader(self, id):
        try:
            self.ChannelIndex[id].join_reader()
        except KeyError:
            raise ChannelPoisonException()

    def Channel_leave_reader(self, id):
        try: 
            self.ChannelIndex[id].leave_reader()
        except KeyError:
            pass

    def Channel_join_writer(self, id):
        try:
            self.ChannelIndex[id].join_writer()
        except KeyError:
            raise ChannelPoisonException()

    def Channel_leave_writer(self, id):
        try:
            self.ChannelIndex[id].leave_writer()
        except KeyError:
            pass

    def test(self):
        return True

class PyroClientManager(object):
    """
    PyroClientManageer is a singleton class.

    The purpose is the handle the connection to a nameserver and to
    create a PyroServerManager if necessary. This PyroServerManager runs
    as a process and functions as a channel server, handling all blocking
    communication.

    >>> A = PyroClientManager()
    >>> B = PyroClientManager()
    >>> A == B
    True
    """

    __instance = None  # the unique instance

    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self):
        pass
    
    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:

            # locate the NS
            Pyro.config.PYRO_NS_DEFAULTGROUP=':PyCSP'
            locator = Pyro.naming.NameServerLocator()

            #Searching Name Server...
            ns = locator.getNS()

            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)
            cls.__instance.nameserver = ns


            def create_server():
                # Create server

                cls.__instance.server_process = PyroServerProcess(ns)

                cls.__instance.server_process.cond.acquire()
                cls.__instance.server_process.daemon = True
                cls.__instance.server_process.start()

                # Wait for server to init
                cls.__instance.server_process.cond.wait()
                cls.__instance.server_process.cond.release()

                URI = ns.resolve('SERVER-'+str(Configuration().get(NET_SERVER_ID)))
                return URI

            try:
                # Fetch URI for server and test
                URI= ns.resolve('SERVER-'+str(Configuration().get(NET_SERVER_ID)))
                server = Pyro.core.getProxyForURI(URI)
                server.test()

            except Pyro.errors.ProtocolError:
                ns.unregister('SERVER-'+str(Configuration().get(NET_SERVER_ID)))
                URI = create_server()

            except Pyro.errors.NamingError:
                try:
                    ns.unregister('SERVER-'+str(Configuration().get(NET_SERVER_ID)))
                except Pyro.errors.NamingError:
                    pass
                URI = create_server()

            cls.__instance.URI = URI
            cls.__instance.server = Pyro.core.getProxyForURI(URI)

            # Found nameserver and daemon
            

        return cls.__instance
    getInstance = classmethod(getInstance)


class Channel:
    """ Channel class with Pyro support. Blocking communication
    
    >>> from __init__ import *

    >>> @process
    ... def P1(cout):
    ...     while True:
    ...         cout('Hello World')

    >>> C = Channel()
    >>> Spawn(P1(OUT(C)))
    
    >>> cin = IN(C)
    >>> cin()
    'Hello World'

    >>> retire(cin)
    """
    def __init__(self, name=None):
        self.URI = PyroClientManager().URI
        server = Pyro.core.getProxyForURI(self.URI)

        ok = False
        while not ok:
            try:
                self.name = server.Channel(name)
                ok = True
            except Pyro.errors.ProtocolError:
                # Connection refused. Try again
                server.adapter.rebindURI()


    def _read(self):
        server = Pyro.core.getProxyForURI(self.URI)
        #print '_read',server

        ok = False
        while not ok:
            try: 
                result = server.Channel_read(self.name)
                ok = True
            except Pyro.errors.ProtocolError:
                # Connection refused. Try again
                server.adapter.rebindURI()
        return result

    def _write(self, msg):
        server = Pyro.core.getProxyForURI(self.URI)
        #print '_write',server

        ok = False
        while not ok:
            try: 
                result = server.Channel_write(self.name, msg)
                ok = True
            except Pyro.errors.ProtocolError:
                # Connection refused. Try again
                server.adapter.rebindURI()
    
        return result

    def poison(self):
        server = Pyro.core.getProxyForURI(self.URI)

        ok = False
        while not ok:
            try: 
                server.Channel_poison(self.name)
                ok = True
            except Pyro.errors.ProtocolError:
                # Connection refused. Try again
                server.adapter.rebindURI()    

    def join_reader(self):
        server = Pyro.core.getProxyForURI(self.URI)
        ok = False
        while not ok:
            try:
                server.Channel_join_reader(self.name)
                ok = True
            except Pyro.errors.ProtocolError:
                # Connection refused. Try again
                server.adapter.rebindURI()

    def leave_reader(self):
        server = Pyro.core.getProxyForURI(self.URI)
        ok = False
        while not ok:
            try:
                server.Channel_leave_reader(self.name)
                ok = True
            except Pyro.errors.ProtocolError:
                # Connection refused. Try again
                server.adapter.rebindURI()

    def join_writer(self):
        server = Pyro.core.getProxyForURI(self.URI)
        ok = False
        while not ok:
            try:
                server.Channel_join_writer(self.name)
                ok = True
            except Pyro.errors.ProtocolError:
                # Connection refused. Try again
                server.adapter.rebindURI()

    def leave_writer(self):
        server = Pyro.core.getProxyForURI(self.URI)
        ok = False
        while not ok:
            try:
                server.Channel_leave_writer(self.name)
                ok = True
            except Pyro.errors.ProtocolError:
                # Connection refused. Try again
                server.adapter.rebindURI()

class Alternation:
    """
    Alternation class with Pyro support

    Alternation supports input and output guards. Guards are ChannelEnd
    or Guard objects.
    
    Note that alternation always performs the guard that was chosen,
    i.e. channel input or output is executed within the alternation so
    even the empty choice with an alternation execution or a choice where
    the results are simply ignored, still performs the guarded input or
    output.

    >>> from __init__ import *

    >>> L = []

    >>> @choice 
    ... def action(ChannelInput):
    ...     L.append(ChannelInput)

    >>> @process
    ... def P1(cout, n=5):
    ...     for i in range(n):
    ...         cout(i)
    
    >>> @process
    ... def P2(cin1, cin2, n=10):
    ...     alt = Alternation([{cin1:action, cin2:action}])
    ...     for i in range(n):
    ...         alt.execute()
                
    >>> C1, C2 = Channel(), Channel()
    >>> Parallel(P1(OUT(C1)), P1(OUT(C2)), P2(IN(C1), IN(C2)))

    >>> len(L)
    10

    >>> L.sort()
    >>> L
    [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
    """
    def __init__(self, guards):
        self.id = None
        self.URI = PyroClientManager().URI
        self.guards = guards

        reduced_guards = []
        for prioritized_item in self.guards:
            reduced_D = {}
            for choice in prioritized_item.keys():
                msg = None
                if type(choice)==tuple:
                    op = WRITE
                    c, msg = choice
                else:
                    op = READ
                    c = choice
                
                if isinstance(c, Guard):
                    reduced_D[c] = (op, msg)
                else:
                    reduced_D[c.channel.name] = (op, msg)

            reduced_guards.append(reduced_D)

        server = Pyro.core.getProxyForURI(self.URI)
        ok = False
        while not ok:
            try:
                self.id = server.Alternation(reduced_guards)
                ok = True
            except Pyro.errors.ProtocolError:
                # Connection refused. Try again
                server.adapter.rebindURI()

    def __del__(self):
        if not self.id == None:
            server = Pyro.core.getProxyForURI(self.URI)
            ok = False
            while not ok:
                try:
                    server.Alternation_delete(self.id)
                    ok = True
                except Pyro.errors.ProtocolError:
                    # Connection refused. Try again
                    server.adapter.rebindURI()


    def choose(self):
        server = Pyro.core.getProxyForURI(self.URI)
        result = None
        while result == None:
            try:
                result = server.Alternation_choose(self.id)
            except Pyro.errors.ProtocolError:
                # Connection refused. Try again
                server.adapter.rebindURI()
        return result
        

    def execute(self):
        """
        Selects the guard and executes the attached action. Action is a function or python code passed in a string.

        >>> from __init__ import *
        >>> L1,L2 = [],[]

        >>> @process
        ... def P1(cout, n):
        ...     for i in range(n):
        ...         cout(i)

        >>> @process
        ... def P2(cin1, cin2, n):
        ...     alt = Alternation([{
        ...               cin1:"L1.append(ChannelInput)",
        ...               cin2:"L2.append(ChannelInput)"
        ...           }])
        ...     for i in range(n):
        ...         alt.execute()

        >>> C1, C2 = Channel(), Channel()
        >>> Parallel(P1(OUT(C1),n=10), P1(OUT(C2),n=5), P2(IN(C1), IN(C2), n=15))

        >>> len(L1), len(L2)
        (10, 5)
        """
        pri_idx, c, msg, op = self.choose()
        c, action = self.get_guard(pri_idx, c)
        
        if action:
            if callable(action):
                # Execute callback function
                if op==WRITE:
                    action()
                else:
                    action(ChannelInput=msg)
            else:
                # Fetch process frame and namespace
                processframe= inspect.currentframe().f_back
                
                # Compile source provided in a string.
                code = compile(action,processframe.f_code.co_filename + ' line ' + str(processframe.f_lineno) + ' in string' ,'exec')
                f_globals = processframe.f_globals
                f_locals = processframe.f_locals
                if not op==WRITE:
                    f_locals.update({'ChannelInput':msg})

                # Execute action
                exec(code, f_globals, f_locals)

    def select(self):
        """
        Selects the guard.

        >>> from __init__ import *
        >>> L1,L2 = [],[]

        >>> @process
        ... def P1(cout, n=5):
        ...     for i in range(n):
        ...         cout(i)

        >>> @process
        ... def P2(cin1, cin2, n=10):
        ...     alt = Alternation([{
        ...               cin1:None,
        ...               cin2:None
        ...           }])
        ...     for i in range(n):
        ...         (g, msg) = alt.select()
        ...         if g == cin1:
        ...             L1.append(msg)
        ...         if g == cin2:
        ...             L2.append(msg)

        >>> C1, C2 = Channel(), Channel()
        >>> Parallel(P1(OUT(C1)), P1(OUT(C2)), P2(IN(C1), IN(C2)))

        >>> len(L1), len(L2)
        (5, 5)
        """

        pri_idx, c, msg, op = self.choose()
        c, action = self.get_guard(pri_idx, c)

        return (c, msg)
    
    def get_guard(self, pri_idx, c_result):
        if isinstance(c_result, Guard):                    
            for choice in self.guards[pri_idx].keys():
                if type(choice)==tuple:
                    if choice[0].id == c_result.id:
                        return choice[0], self.guards[pri_idx][choice]
                else:
                    if choice.id == c_result.id:
                        return choice, self.guards[pri_idx][choice]
        else:
            for choice in self.guards[pri_idx].keys():
                if type(choice)==tuple:
                    if choice[0].channel.name == c_result:
                        return choice[0], self.guards[pri_idx][choice]
                else:
                    if choice.channel.name == c_result:
                        return choice, self.guards[pri_idx][choice]
        
        raise Exception('Internal Error: Could not find guard in alternation guard list')
                    
                
# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
