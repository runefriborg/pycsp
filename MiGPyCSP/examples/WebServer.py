"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>
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
from pycsp_import import *
import socket
import time
import sys

if sys.platform == 'win32' and (version[3] == 'processes'):
    print 'This example creates nested processes and channels, which is not supported in win32, when using processes implementation'
    sys.exit(0)

@process
def HelloWorld(register):
    request_channel = Channel('HelloWorld'+str(id))
    cin = +request_channel
    register(('/hello.html', -request_channel))
    while True:
        (request_string, cout) = cin()
        cout("Hello at " + time.strftime("%H:%M:%S", time.localtime()))

@process
def Time(register):
    request_chan = Channel('Time-'+str(id))
    cin = +request_chan
    register(('/time.html', -request_chan))

    while True:
        (request_string, cout) = cin()
        cout(str(time.time()))

@process
def Index(id, register):
    request_chan = Channel('Index-'+str(id))
    cin = +request_chan
    register(('/index.html', -request_chan))
    register(('/', -request_chan))

    while True:
        (request_string, cout) = cin()
        s = "Hello World! :" + request_string
        s += "<br>Visit <a href='time.html'>time</a> or <a href='sleep.html?5'>sleep</a>"
        s += "<br><br>Served by process " + str(id)
        cout(s)

@io
def time_sleep(s):
    import time
    time.sleep(s)

@process
def Sleep(id, register):
    request_chan = Channel('Sleep-'+str(id))
    cin = +request_chan
    register(('/sleep.html', -request_chan))

    while True:
        (request_string, cout) = cin()
        seconds = 0
        if request_string.find('?') != -1:
            try:
                seconds = int(request_string[request_string.index('?')+1:])
            except Exception, e:
                print e

        if type(seconds) == type(0):
            s = "Process " + str(id) + " is going to sleep for " +str(seconds) + " seconds"
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

        print 'Dispather got:',GET,result

        if GET.find('?') != -1:
            service_id = GET[:GET.index('?')]
        else:
            service_id = GET

        # Dispatch to service by Alternating on output ends.
        if services.has_key(service_id):
            guards = []
            for req in services[service_id]:
                guards.append( OutputGuard(req, msg=(GET, result)) )
            AltSelect(*guards)
        else:
            result("Service '"+str(service_id)+"' not found!<br>")
        
    def add_service(channel_input):
        (id, request) = channel_input
        if services.has_key(id):
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
        poison(*services.values())

@process
def HTTPsocket(sock, dispatchChan):
    answer='HTTP/1.0 200 OK\nServer: BaseHTTP/0.2 Python/2.2\nDate: Tue, 18 Feb 2003 17:15:49 GMT\nContent-Type: text/html\nServer: myHandler\n\n'

    item = Channel()
    itemOut = -item
    itemIn = +item

    conn, addr=sock
    req=conn.recv(256)
    if not req:
        conn.close()
        return
    lines = req.split('\n')
    for line in lines:
        line=line.split(' ')
        if line[0]=='GET':
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
    serversocket.bind(('', 8080))
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

