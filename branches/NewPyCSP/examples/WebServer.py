from common import *
from pycsp import *
import socket
import time
import sys

@process
def Time(register):
    request_chan = Channel()
    cin = IN(request_chan)
    register(('/time.html', OUT(request_chan)))
    while True:
        (request_string, cout) = cin()
        cout(str(time.time()))

@process
def Index(register):
    request_chan = Channel()
    cin = IN(request_chan)
    register(('/index.html', OUT(request_chan)))
    register(('/', OUT(request_chan)))
    while True:
        (request_string, cout) = cin()
        s = "Hello World! :" + request_string

        import threading
        s += "<br><br>Served by thread " + str(threading.currentThread()).replace('<','&lt;').replace('>','&gt;')

        cout(s)

@process
def Dispatcher(register, inc):
    services = {}

    def dispatch(ChannelInput):
        (GET, result) = ChannelInput
        print GET
        if GET.find('?') != -1:
            service_id = GET[:GET.index('?')]
        else:
            service_id = GET

        # Dispatch to service by Alternating on output ends.
        if services.has_key(service_id):
            request_alternation = {}
            for req in services[service_id]:
                request_alternation[(req,(GET, result))] = None
            Alternation([request_alternation]).execute()
        else:
            result("Service not found!<br>")
        
    def add_service(ChannelInput):
        (id, request) = ChannelInput
        if services.has_key(id):
            services[id].append(request)
        else:
            services[id] = [request]

    try:
        while True:
            Alternation([{
                    register:add_service,
                    inc:dispatch
                  }]).execute()

    except ChannelPoisonException:
        poison(register, inc)
        poison(*services.values())

@process
def HTTPsocket(inc, dispatchChan):
    answer='HTTP/1.0 200 OK\nServer: BaseHTTP/0.2 Python/2.2\nDate: Tue, 18 Feb 2003 17:15:49 GMT\nContent-Type: text/html\nServer: myHandler\n\n'

    item = Channel()
    itemOut = OUT(item)
    itemIn = IN(item)

    while True:
        conn, addr=inc()
        req=conn.recv(256)
        if not req:
            return
        lines = req.split('\n')
        for line in lines:
            line=line.split(' ')
            if line[0]=='GET':
                conn.sendall(answer)
                dispatchChan((line[1], itemOut))
                conn.sendall(itemIn())
        conn.close()

@process
def entry(outc):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('', 8080))
    serversocket.listen(1)
    
    while True:
        outc(serversocket.accept())


c=Channel()
register=Channel()
request=Channel()

Parallel(entry(OUT(c)),
         [HTTPsocket(IN(c), OUT(request)) for i in range(10)],
         Dispatcher(IN(register), IN(request)),
         [Time(OUT(register)) for i in range(5)],
         [Index(OUT(register)) for i in range(5)])

