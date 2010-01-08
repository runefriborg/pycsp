#!/usr/bin/env python
"""
./pycsp-run.py [arguments] file.csp
A distributed run environment similar to mpi-run,
but specifically for executing PyCSP applications.

Copyright (c) 2009 Rune M. Friborg, runef@diku.dk.
See LICENSE.txt for licensing details.
"""

### Imports
import os, sys
import subprocess

### Read hosts
hosts = []
if os.path.isfile('pycsphost'):
    fp = open('pycsphost', 'r')
    lines = fp.readlines()
    hosts = map(str.strip, lines)

if len(hosts) == 0:
    print 'No hosts found'
    sys.exit(0)

### Get hostname
p = subprocess.Popen(['/usr/bin/env', 'hostname'], stdout=subprocess.PIPE)
stdoutdata, stderrdata = p.communicate()
HOSTNAME = stdoutdata.strip()

def kill(host):
    if host == 'localhost' or host == HOSTNAME:
        p = subprocess.Popen(["sh", "-c", "ps ax | grep 'run_from_daemon' | awk '{print $1}' | xargs kill -9"], stdout = subprocess.PIPE, stderr = subprocess.PIPE) 
        (stdoutdata, stderrdata) = p.communicate()
    else:
        p = subprocess.Popen(["ssh", h, "ps ax | grep 'run_from_daemon' | awk '{print $1}' | xargs kill -9"], stdout = subprocess.PIPE, stderr = subprocess.PIPE) 
        (stdoutdata, stderrdata) = p.communicate()
    print 'out',stdoutdata
    print 'err',stderrdata

for h in hosts:
    kill(h)


