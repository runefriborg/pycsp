#!/usr/bin/env python

from pycsp import daemonNet
import sys
import subprocess

import os
os.environ['PYCSP'] = 'DIST'

daemonNet.Configuration().set(daemonNet.NET_SERVER_ID, 'daemonNet')
secretKey = sys.stdin.readline().strip()

@daemonNet.process
def execute(package):
    func_name, file, pickled_args, reply = package
    print 'Executing', func_name
    p = subprocess.Popen(['/usr/bin/env', 'python', file, 'run_from_daemon', func_name], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    stdoutdata, stderrdata = p.communicate(pickled_args)
    if reply != None:
        reply((stdoutdata, stderrdata))

@daemonNet.process
def receive(any):
    try:
        while True:
            # Here we use Alternation to receive from multiple channels.
            # When a package has been received we check the secretKey
            key, package = any()
            if key == secretKey:
                daemonNet.Spawn(execute(package))
            else:
                _, _, _, reply = package
                if reply != None:
                    daemonNet.Spawn(daemonNet.Process(reply, (None, 'Unauthorized access!\n')))
    except daemonNet.ChannelPoisonException:
        print 'Shutting Down'
        

daemonNet.Parallel(receive(daemonNet.Channel('AnyDaemon').reader()))
