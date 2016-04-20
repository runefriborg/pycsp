"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *
import socket
import time
import sys

PORT = 8081

@process
def HelloWorld(register):
    request_channel = Channel('HelloWorld'+str(id))
    cin = +request_channel
    register((b'/hello.html', -request_channel))
    while True:
        (request_string, cout) = cin()
        cout(b"Hello at " + time.strftime("%H:%M:%S", time.localtime()).encode())

@process
def Time(register):
    request_chan = Channel('Time-'+str(id))
    cin = +request_chan
    register((b'/time.html', -request_chan))

    while True:
        (request_string, cout) = cin()
        cout(str(time.time()).encode())

@process
def Index(id, register):
    request_chan = Channel('Index-'+str(id))
    cin = +request_chan
    register((b'/index.html', -request_chan))
    register((b'/', -request_chan))

    while True:
        (request_string, cout) = cin()
        s = b"Hello World! :" + request_string
        s += b"<br>Visit <a href='time.html'>time</a> or <a href='sleep.html?5'>sleep</a>"
        s += b"<br><br>Served by process " + str(id).encode()
        cout(s)

@io
def time_sleep(s):
    import time
    time.sleep(s)

@process
def Sleep(id, register):
    request_chan = Channel('Sleep-'+str(id))
    cin = +request_chan
    register((b'/sleep.html', -request_chan))

    while True:
        (request_string, cout) = cin()
        seconds = 0
        if request_string.find(b'?') != -1:
            try:
                seconds = int(request_string[request_string.index(b'?')+1:])
            except Exception as e:
                print(e)

        if type(seconds) == type(0):
            s = b"Process " + str(id).encode() + b" is going to sleep for " +str(seconds).encode() + b" seconds"
            cout(s)

            time_sleep(seconds)

        else:
            s = str(ms) + " is not a number!"
            cout(s)

        
        

@process
def Dispatcher(register, inc):
    services = {}

    def dispatch(channel_input):
        (GET, result) = channel_input

        print(b'Dispather got:',GET,result)

        if GET.find(b'?') != -1:
            service_id = GET[:GET.index(b'?')]
        else:
            service_id = GET

        # Dispatch to service by Alternating on output ends.
        if service_id in services:
            guards = []
            for req in services[service_id]:
                guards.append( OutputGuard(req, msg=(GET, result)) )
            AltSelect(*guards)
        else:
            result(b"Service '"+str(service_id).encode() + b"' not found!<br>")
        
    def add_service(channel_input):
        (id, request) = channel_input
        if id in services:
            services[id].append(request)
        else:
            services[id] = [request]

    try:
        while True:
            AltSelect(
                    InputGuard(register, action=add_service),
                    InputGuard(inc, action=dispatch)
                    )
                
    except ChannelPoisonException:
        poison(register, inc)
        for regs in list(services.values()):
            poison(*regs)

@process
def HTTPsocket(sock, dispatchChan):
    answer=b'HTTP/1.0 200 OK\nServer: BaseHTTP/0.2 Python/2.2\nDate: Tue, 18 Feb 2003 17:15:49 GMT\nContent-Type: text/html\nServer: myHandler\n\n'

    item = Channel()
    itemOut = -item
    itemIn = +item

    conn, addr=sock
    req=conn.recv(256)
    if not req:
        conn.close()
        return
    lines = req.split(b'\n')
    for line in lines:
        line=line.split(b' ')
        if line[0]==b'GET':
            conn.sendall(answer)
            dispatchChan((line[1], itemOut))
            conn.sendall(itemIn())

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()


@io
def serversocket_accept(serversocket):
    return serversocket.accept()
    
@process
def entry(request):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Enable reuse of sockets in TIME_WAIT state.  
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    serversocket.bind(('', PORT))

    print(("Listening on http://localhost:" + str(PORT)))
    
    serversocket.listen(1)
    
    while True:
        s = serversocket_accept(serversocket)
        Spawn(HTTPsocket(s, -request))


register=Channel('Register Service')
request=Channel('Request Service')

Parallel(entry(request),
         Dispatcher(+register, +request),
         [Time(-register) for i in range(2)],
         [Sleep(i, -register) for i in range(50)],
         [Index(i, -register) for i in range(2)],
         HelloWorld(-register))

shutdown()
