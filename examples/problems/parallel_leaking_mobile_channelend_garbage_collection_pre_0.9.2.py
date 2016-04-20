"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>
"""

import sys
from pycsp_import import *
from random import randint

# Running this multiple times, eventually causes a deadlock with output looking like this:
# python parallel_leaking_mobile_channelend_garbage_collection.py 
# 192.168.0.12 80
# 192.168.0.12 80
# 192.168.0.12 80
# Simulated HTTP Server got:  Hello?705
# 192.168.0.12 80
# ...
# ...
# Simulated HTTP Server got:  Hello?910
# Simulated HTTP Server got:  Hello?480
# Bye
# Simulated HTTP Server got:  Hello?43
# Simulated HTTP Server got:  Hello?910
# Bye
# Bye

@process
def do_service(outp):
        conn = Channel()
        outp(conn.writer())
        inp = conn.reader()

        while True:
                msg = inp()
                outp('Simulated HTTP Server got:  '+msg)
                #outp.disconnect() / explicit disconnect was necessary, before this was fixed.

@process
def server(IPin):
        for _ in range(10):       #Only do 10 services then terminate
                addr, port, conn = IPin()
                print(addr,port)
                Spawn(do_service(conn))

        print('Major bye')

@process
def client(IPout):
        id = randint(0,1000)
        conn = Channel()
        IPout(('192.168.0.12',80,conn.writer()))
        
        inp = conn.reader()
        # Receiving new channel end
        outp = inp()
       
        for _ in range(10):
                outp('Hello?%d'%id)
                msg = inp()
                print(msg)
        print('Bye')
        poison(outp)

service = Channel()

Parallel(server(service.reader()), 10*client(service.writer()))
print('Parallel returned...')

shutdown()
