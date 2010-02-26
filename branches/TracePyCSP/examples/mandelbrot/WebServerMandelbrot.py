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
from pycsp.common.trace import *

import socket
import time
import sys
from numpy import *
from ctypes import *
import png
import cStringIO

mandelbrot=CDLL('mandelbrot_kernel.dylib')

TraceInit()

if sys.platform == 'win32' and (version[3] == 'processes'):
    print 'This example creates nested processes and channels, which is not supported in win32, when using processes implementation'
    sys.exit(0)



def init_time_record():
    return {'total':0,'diff':time.time(),'calls':0}

def t1(record):
    record['diff'] = time.time()
    record['calls'] += 1

def t2(record):
    record['total'] += time.time() - record['diff']
    record['diff'] = -9999

def compute(u, h_step, w_step, h_start, w_start, h, w, maxit):
    mandelbrot.compute(u.ctypes.data_as(c_void_p),
                       c_double(h_step),
                       c_double(w_step),
                       c_double(h_start),
                       c_double(w_start),
                       c_int(h),
                       c_int(w),
                       c_int(maxit))
    



@process
def worker(cin, cout, maxit = 5000):
    time_rec = init_time_record()
    try:
        while True:
            (id, w_start, w_step, w, h_start, h_step, h) = cin()
            t1(time_rec)

            u=zeros((h,w), dtype=uint16)
            compute(u, h_step, w_step, h_start, w_start, h, w, maxit)

            t2(time_rec)
            cout((id, u))
    except ChannelPoisonException:
        sys.stdout.write('  Worker: %d calls, %fs\n' % (time_rec['calls'],time_rec['total']))


@process
def manager(workerOut, workerIn, send_result, w, h):

    jobcount = w/100
    time_rec = init_time_record()

    #xmin = -2.0
    #xmax = 0.8
    #ymin = -1.4
    #ymax = 1.4
        
    xmin = -1.6744096758873175
    xmax = -1.6744096714940624
    ymin = 0.00004716419197284976
    ymax = 0.000047167062611931696

    w_step = (xmax-xmin)/w
    h_step = (ymax-ymin)/h
    w_start = xmin
    h_start = ymin

    job_h = h/jobcount

    # Generate jobs
    # Tuple: (job_id, w_start, w_step, width, h_start(job), h_step, job_h)
    jobs = []
    for job_id in xrange(jobcount):
        jobs.append(
            (job_id,
             w_start, w_step, w,
             h_start + h_step * (job_id * job_h), h_step, job_h)
            )

    if job_h*jobcount < h:
        last_h = h - job_h*jobcount
        jobs.append(
            (jobcount,
             w_start, w_step, w,
             h_start + h_step*(jobcount*job_h), h_step, last_h))

    jobcount = len(jobs)

    # Deliver and receive
    results = [None for i in range(jobcount)]
    received = 0
    while jobs or received < jobcount:
        t2(time_rec)
        if jobs:
            guard, msg = Alternation([
                        (workerIn, None),
                        (workerOut, jobs[-1], "jobs.pop(-1)")
                        ]).execute()

        else:
            guard = workerIn
            msg = guard()
        t1(time_rec)

        if guard == workerIn:
            job_id, result = msg
            received += 1
            results[job_id] = result        

    # Produce result                
    u = concatenate(results, axis=0)
    u = concatenate(u, axis=0)
    u = uint16(u / (u.max()/255.0))

    img = png.Writer(w, h, greyscale=1)
    stream = cStringIO.StringIO()
    img.write_array(stream, u)

    sys.stdout.write('  Manager: %fs\n' % (time_rec['total']))

    send_result(stream.getvalue())
    stream.close()

    retire(workerIn, workerOut)

@process
def Mandelbrot(id, register):    
    answer='HTTP/1.0 200 OK\nServer: BaseHTTP/0.2 Python/2.2\nDate: Tue, 18 Feb 2003 17:15:49 GMT\nContent-Type: image/png\nServer: myHandler\n\n'
    request_chan = Channel('Mandelbrot-'+str(id))
    cin = request_chan.reader()
    register(('/mandelbrot.html', request_chan.writer()))
    while True:
        (request_string, cout) = cin()
        
        workers = 5
        width, height = 1000, 1000
        
        jobChannel = Channel()
        resultChannel = Channel()

        Parallel(manager(jobChannel.writer(), resultChannel.reader(), cout, width, height),
                 [worker(jobChannel.reader(), resultChannel.writer()) for i in range(workers)])
        
        #cout(s)


@process
def Index(id, register):
    answer='HTTP/1.0 200 OK\nServer: BaseHTTP/0.2 Python/2.2\nDate: Tue, 18 Feb 2003 17:15:49 GMT\nContent-Type: text/html\nServer: myHandler\n\n'

    request_chan = Channel('Index-'+str(id))
    cin = request_chan.reader()
    register(('/index.html', request_chan.writer()))
    register(('/', request_chan.writer()))

    while True:
        (request_string, cout) = cin()
        s = answer
        s += "Hello World! :" + request_string
        s += "<br>Visit <a href='time.html'>time</a> or <a href='sleep.html?5'>sleep</a>"
        s += "<br><br>Served by process " + str(id)
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
            request_alternation = {}
            for req in services[service_id]:
                request_alternation[(req,(GET, result))] = None
            Alternation([request_alternation]).select()

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
            Alternation([{
                    register:add_service,
                    inc:dispatch
                  }]).execute()

    except ChannelPoisonException:
        poison(register, inc)
        poison(*services.values())

@process
def HTTPsocket(sock, dispatchChan):

    item = Channel()
    itemOut = item.writer()
    itemIn = item.reader()

    conn, addr=sock
    req=conn.recv(256)
    if not req:
        conn.close()
        return
    lines = req.split('\n')
    for line in lines:
        line=line.split(' ')
        if line[0]=='GET':
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
    serversocket.bind(('', 8081))
    serversocket.listen(1)
    
    while True:
        s = serversocket_accept(serversocket)
        Spawn(HTTPsocket(s, request.writer()))


register=Channel('Register Service')
request=Channel('Request Service')

Parallel(entry(request),
         Dispatcher(register.reader(), request.reader()),
         [Mandelbrot(i, register.writer()) for i in range(2)],
         [Index(i, register.writer()) for i in range(2)]
         )

