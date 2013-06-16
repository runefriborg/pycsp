"""
Constructs added to allow easy switching between PyCSP implementations.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp.greenlets.exceptions import *

def shutdown():
    """
    Perform shutdown of non-active hosted channels. Wait
    for active hosted channels to become non-active.
    """
    return

def multiprocess(func=None, pycsp_host='', pycsp_port=None):
    raise InfoException("multiprocess not available for greenlets. Use pycsp.parallel")

class MultiProcess():
    def __init__(self, fn, *args, **kwargs):
        raise InfoException("MultiProcess not available for greenlets. Use pycsp.parallel")

def sshprocess(func=None, pycsp_host='', pycsp_port=0, ssh_host='localhost', ssh_port=22, ssh_user=None, ssh_password=None, ssh_python='python'):
    raise InfoException("sshprocess not available for greenlets. Use pycsp.parallel")

class SSHProcess():
    def __init__(self, fn, *args, **kwargs):
        raise InfoException("SSHProcess not available for greenlets. Use pycsp.parallel")

def clusterprocess(func=None, cluster_nodefile="$PBS_NODEFILE", cluster_pin=None, cluster_hint='blocked', cluster_ssh_port=22, cluster_python='python'):
    raise InfoException("clusterprocess not available for greenlets. Use pycsp.parallel")

class ClusterProcess():
    def __init__(self, fn, *args, **kwargs):
        raise InfoException("ClusterProcess not available for greenlets. Use pycsp.parallel")

class ChannelSocketException(Exception):
    def __init__(self, addr, msg):
        self.msg = msg
        self.addr = addr
    def __str__(self):
        return repr("%s %s" % (self.msg, self.addr))


SOCKETS_CONNECT_TIMEOUT = 0
SOCKETS_CONNECT_RETRY_DELAY = 1
SOCKETS_BIND_TIMEOUT = 2
SOCKETS_BIND_RETRY_DELAY = 3
PYCSP_PORT = 5
PYCSP_HOST = 6
SOCKETS_STRICT_MODE = 4

class Configuration(object):
    """
    This is dummy Configuration class, as the greenlets
    does not require any configuration.
    """
    __instance = None  # the unique instance
    __conf = {}

    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self):
        pass
    
    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:
            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)
            
            cls.__conf = {
                SOCKETS_CONNECT_TIMEOUT:0,
                SOCKETS_CONNECT_RETRY_DELAY:0,
                SOCKETS_BIND_TIMEOUT:0,
                SOCKETS_BIND_RETRY_DELAY:0,
                PYCSP_PORT:0,
                PYCSP_HOST:'',
                SOCKETS_STRICT_MODE:False
                }
            
        return cls.__instance
    getInstance = classmethod(getInstance)

    def get(self, conf_id):
        return self.__conf[conf_id]

    def set(self, conf_id, value):
        self.__conf[conf_id] = value

        
