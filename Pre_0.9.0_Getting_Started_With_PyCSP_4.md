# A Scalable Webserver #

Contents:


## Answer request on port 8080 ##

```
import pycsp

@pycsp.process
def HTTPsocket(sock):
    answer= 'HTTP/1.0...'

    conn, addr=sock
    req=conn.recv(256)
    if req:
        lines = req.split('\n')
        for line in lines:
            line=line.split(' ')
            if line[0]=='GET':
                conn.sendall(answer)
                conn.sendall("Hello from HTTPSocket");

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()

@pycsp.process
def Entry():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('', 8080))
    serversocket.listen(1)
    while True:
        s = serversocket.accept()
        pycsp.Spawn( HTTPsocket(s) )

pycsp.Parallel( Entry() )
```

<img src='http://pycsp.googlecode.com/files/WebserverStep1.png' width='400'>

<h2>Adding a Hello World service</h2>

<pre><code>import pycsp<br>
<br>
@pycsp.process<br>
def HelloWorld(request):<br>
    while True:<br>
        (request_string, cout) = request()<br>
        cout("Hello World at "+time.strftime("%H:%M:%S",  \\ time.localtime()))<br>
<br>
@pycsp.process<br>
def HTTPsocket(sock, sendRequest):<br>
 [snip]<br>
    for line in lines:<br>
        line=line.split(' ')<br>
        if line[0]=='GET':<br>
            conn.sendall(answer)<br>
            sendRequest((line[1], itemOut))<br>
            conn.sendall(itemIn())<br>
 [snip]<br>
<br>
@pycsp.process<br>
def Entry(dispatch):<br>
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)<br>
    serversocket.bind(('', int(sys.argv[1])))<br>
    serversocket.listen(1)<br>
    while True:<br>
        s = serversocket.accept()<br>
        pycsp.Spawn( HTTPsocket(s, dispatch) )<br>
<br>
requestChan = pycsp.Channel('Request')<br>
<br>
pycsp.Parallel( <br>
    Entry(requestChan.writer()),<br>
    HelloWorld(requestChan.reader())<br>
    )<br>
</code></pre>
<img src='http://pycsp.googlecode.com/files/WebserverStep2.png' width='400'>

<h2>Adding More Services</h2>
<pre><code>import pycsp<br>
<br>
@pycsp.process<br>
def Sleep5sec(id, request):<br>
    seconds = 5 <br>
    while True:<br>
        (request_string, cout) = request()<br>
        s = "Process " + str(id)<br>
        s += " is going to sleep for " +str(seconds) + " seconds"<br>
        cout(s)<br>
        time.sleep(seconds)<br>
<br>
pycsp.Parallel( <br>
    Entry(requestChan.writer()),<br>
    [ Sleep5sec(id, requestChan.reader()) for id in range(3) ]<br>
    )<br>
</code></pre>

<img src='http://pycsp.googlecode.com/files/WebserverStep3.png' width='400'>

<h2>Adding a Service Dispatcher</h2>
<pre><code>import pycsp<br>
<br>
@pycsp.process<br>
def HelloWorld(register):<br>
    req = pycsp.Channel()<br>
    cin = req.reader()<br>
    register(('/hello.html', req.writer()))<br>
    while True:<br>
        (request_string, cout) = cin()<br>
        cout("Hello World at " + time.strftime("%H:%M:%S", time.localtime()))<br>
<br>
@pycsp.process<br>
def Dispatcher(register, incoming_request):<br>
    services = {}<br>
    while True:<br>
        pycsp.AltSelect(<br>
           pycsp.InputGuard(register, action=add_service(services)),<br>
           pycsp.InputGuard(incoming_request,<br>
					action=dispatch(services))<br>
        )<br>
<br>
@pycsp.choice<br>
def add_service(services, channel_input=None):<br>
    (id, requestChEnd) = channel_input<br>
    if services.has_key(id):<br>
        services[id].append(requestChEnd)<br>
    else:<br>
        services[id] = [requestChEnd]<br>
<br>
@pycsp.choice<br>
def dispatch(services, channel_input = None):<br>
    (GET, resultChEnd) = channel_input<br>
    if GET.find('?') != -1:<br>
        service_id = GET[:GET.index('?')]<br>
    else:<br>
        service_id = GET<br>
<br>
    # Dispatch to service by Alting on output ends.<br>
    if services.has_key(service_id):<br>
        guards = []<br>
        for req in services[service_id]:<br>
            guards.append( OutputGuard(req, msg=(GET, resultChEnd)) )<br>
        pycsp.AltSelect(*guards)<br>
    else:<br>
        resultChEnd("Service '"+str(service_id)+"' not found!&lt;br&gt;")<br>
<br>
pycsp.Parallel( <br>
    Entry(requestChan.writer()),<br>
    Dispatcher(registerChan.reader(), requestChan.reader()),<br>
    [ Sleep5sec(id, registerChan.writer()) for id in range(3) ],<br>
    [Index(id, registerChan.writer()) for id in range(2)],<br>
    HelloWorld(registerChan.writer()))<br>
</code></pre>

<img src='http://pycsp.googlecode.com/files/WebserverStep4.png' width='600'>

<h2>Adding a pool of HTTPsocket processes</h2>
<pre><code>import pycsp<br>
<br>
@pycsp.process<br>
def HTTPsocket(getSocket, sendRequest):<br>
    [snip]<br>
    while True:<br>
        conn, addr= getSocket()<br>
        req=conn.recv(256)<br>
        if not req:<br>
            conn.close()<br>
            return<br>
        lines = req.split('\n')<br>
        for line in lines:<br>
            line=line.split(' ')<br>
            if line[0]=='GET':<br>
                conn.sendall(answer)<br>
                sendRequest((line[1], itemOut))<br>
                conn.sendall(itemIn())<br>
<br>
@pycsp.process<br>
def Entry(dispatch):<br>
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)<br>
    serversocket.bind(('', int(sys.argv[1])))<br>
    serversocket.listen(1)<br>
<br>
    socketChan = pycsp.Channel('Socket Channel')<br>
    sendSocket = socketChan.writer()<br>
    <br>
    pycsp.Spawn(<br>
        [ HTTPsocket(socketChan.reader(), dispatch) for i in range(8) ]<br>
        )<br>
<br>
    while True:<br>
        s = serversocket.accept()<br>
        sendSocket(s)<br>
</code></pre>

<img src='http://pycsp.googlecode.com/files/WebserverStep5.png' width='800'>