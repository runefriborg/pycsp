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

import sys
sys.path.insert(0, "../..")
from pycsp.parallel import *

import time
import random
import sys

@io
def sleep_random():
    time.sleep(random.random()/10)

@io
def sleep_long_random():
    time.sleep(random.random()*5)


@process
def connect_reader(remote_addr):
    while True:
        try:
            X=Channel('A', connect=remote_addr)            
            cin = X.reader()
            val = cin()
            sys.stdout.write(str(val) + ' ')
            return

        except ChannelConnectException as e:
            sys.stdout.write('.')

@process
def connect_reader_quit(remote_addr):
    while True:
        try:
            X=Channel('A', connect=remote_addr)            
            cin = X.reader()
            val = cin()
            raise Exception("Failed!")

        except ChannelConnectException as e:
            sys.stdout.write('OK')
            return
                

def host_writer(N=1):
    X=Channel('A')
    cout = X.writer()
    for i in range(N):
        cout(i)

def ConnectCatchFailed():
    addr = ('localhost', 22222)
    Parallel(connect_reader_quit(addr))

def BindCatchFailed():
    addr = ('localhost', 22223)
    Spawn(MultiProcess(host_writer, host=addr[0], port=addr[1]))

    # Fail to bind!
    try:
        Parallel(MultiProcess(host_writer, host=addr[0], port=addr[1]))
    except ChannelBindException as e:
        sys.stdout.write('OK')
    
    # Connect to spawned process
    X=Channel('A', connect=addr)
    cin = X.reader()
    X= cin()
    cin.disconnect()

def ConnectOne(sleeper, port):
    addr = ('localhost', port)
    Spawn(connect_reader(addr))
    
    if sleeper:
        sleeper()

    Parallel(MultiProcess(host_writer, host=addr[0], port=addr[1]))

    sys.stdout.write('OK')


def ConnectMultiple(sleeper, port):
    addr = ('localhost', port)
    Spawn(10 * connect_reader(addr))
    
    if sleeper:
        sleeper()

    Parallel(MultiProcess(host_writer, host=addr[0], port=addr[1], N=10))

    sys.stdout.write('OK')
   
if __name__ == '__main__':


    sys.stdout.write("ConnectCatchFailed:")
    ConnectCatchFailed()
    sys.stdout.write("\n")

    sys.stdout.write("BindCatchFailed:")
    BindCatchFailed()
    sys.stdout.write("\n")    

    sys.stdout.write("ConnectOne-sleep_random:")
    ConnectOne(sleep_random, 12346)
    sys.stdout.write("\n")

    sys.stdout.write("ConnectOne-sleep_long_random:")
    ConnectOne(sleep_long_random, 12347)
    sys.stdout.write("\n")

    sys.stdout.write("ConnectMultiple-sleep_random:")
    ConnectMultiple(sleep_random, 12348)
    sys.stdout.write("\n")

    sys.stdout.write("ConnectMultiple-sleep_long_random:")
    ConnectMultiple(sleep_long_random, 12349)
    sys.stdout.write("\n")
    

    shutdown()
