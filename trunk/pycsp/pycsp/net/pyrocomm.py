"""
Support class simplifying usage of Pyro.

Author :        John Markus Bjorndalen <johnm@cs.uit.no>
Version:        1.0

The user of this library should only need to use these functions:

 - get_robject       query name server for object and retrieve proxy object
 - provide_object    register obj with server (server is automatically started)
"""

import sys, socket
import Pyro.naming
import Pyro.core
import threading
import os
from Pyro.errors import PyroError, NamingError

group = ':pycsp_test/' # the namespace for the current test source

# Variables used by the server part
serv_daemon     = None
serv_thread_id  = None
serv_thread_pid = -1

client_initialized = 0
server_initialized = 0

server_wait = 3  # time to sleep before checking kill_server
kill_server = 0  # Flag to let server kill itselv

def modify_uri_host(uri, new_host):
    "Modify the host part of an URI"
    # An uri object should have an address field, should be just a
    # matter of replacing that part
    uri.address = new_host
    return uri

def find_nameserver():
    return Pyro.naming.NameServerLocator().getNS()


def serv_thread():
    "Internal function to run the server daemon."
    sys.stdout.flush()
    global serv_daemon, kill_server, server_wait, serv_thread_pid
    serv_thread_pid = os.getpid()
    while not kill_server:
        # Handle requests, returning every 3 seconds to do another round
        serv_daemon.handleRequests(server_wait)


def init_server():
    "Initialize server side code and spawn a server daemon."
    global serv_daemon, group, server_initialized, serv_thread_id

    if server_initialized:
        return None
    
    print "Initializing server"
    
    Pyro.core.initServer() # Set arg 0 if suppressing server
    Pyro.config.PYRO_NS_DEFAULTGROUP = group

    name_server = find_nameserver()

    # make sure our namespace group exists
    try:
        name_server.createGroup(group)
    except NamingError:
        pass

    serv_daemon = Pyro.core.Daemon()
    serv_daemon.useNameServer(name_server)

    # Start server thread
    serv_thread_id = threading.Thread(target = serv_thread, args = (), name = "server thread")
    serv_thread_id.setDaemon(1)
    serv_thread_id.start()

    server_initialized = 1


def init_client():
    "Initialize client side code."
    # initialize the client and set the default namespace group
    global group, client_initialized

    if client_initialized:
        return None
    
    Pyro.core.initClient()
    Pyro.config.PYRO_NS_DEFAULTGROUP = group

    client_initialized = 1


def _get_robject_uri(obj_name):
    "Get an URI For an object"
    name_server = find_nameserver()
    # resolve the Pyro object
    # print 'binding to object', obj_name
    try:
        URI = name_server.resolve(group + obj_name)
        # print 'URI:',URI
    except Pyro.core.PyroError, x:
        print 'Couldn\'t bind object, nameserver says:', x
        raise SystemExit
    return URI

def get_robject(obj_name, with_attrs = False):
    "Get a proxy for a remote object. The URI can be passed instead of 'obj_name'."
    # create a proxy for the Pyro object, and return that  using dynamic proxy

    init_client()  # Make sure
                
    if isinstance(obj_name, Pyro.core.PyroURI):
        URI = obj_name
    else:
        URI = _get_robject_uri(obj_name)

    if with_attrs:
        return Pyro.core.getAttrProxyForURI(URI)
    else:
        return Pyro.core.getProxyForURI(URI)


def _possibly_delegate(obj):
    """Returns an object that delegates to 'obj' if 'obj' does not inherit
    from Pyros base object"""
    if not isinstance(obj, Pyro.core.ObjBase):
        #print "Delegation needed for ", obj
        slave = Pyro.core.ObjBase()
        slave.delegateTo(obj)
        return slave
    return obj


def provide_object(obj, service_name = None):
    '''Register an object which should provide some service. service_name is
    the hierarchal name of the service.
    If service_name is not provided, the service is not registered with the
    name server. 
    Object does not have to inherit from Pyro.core.ObjBase.
    Returns URI of object and the object (or proxy object if necessary to wrap the original).'''
    global serv_daemon

    init_server()  # Make sure

    # Get delegate object if needed, otherwise original object
    serv_obj = _possibly_delegate(obj)

    if not service_name:
        # Don't register with name server, only register with our daemon
        return (serv_daemon.connect(serv_obj), serv_obj)

    sname = group + service_name
    print "Registering obj as service name", sname
    # Remove old registration (if any) for our name
    name_server = find_nameserver()
    try:
        name_server.unregister(sname)
    except NamingError:
        # It wasn't registered already
        pass 
    return (serv_daemon.connect(serv_obj, sname), serv_obj)

def disconnect_object(obj):
    "De-registers the given object from Pyro (please pass the Pyro or proxy object (see provide_object))."
    serv_daemon.disconnect(obj)

if __name__ == "__main__":
    class foo:
        __doc__ = "nada"
        def __init__(s):
            s._vals = []
        def append(s, obj):
            print "hoi", obj
            s._vals.append(obj)
        def vals(s):
            return s._vals
            
    provide_object(foo(), "lst")
    o = get_robject("lst", False)
    print o
    print o.__doc__
    o.append("a")
    o.append("b")
    print "list is now", o.vals()
