#!/usr/bin/env python
"""
./pycsp-run.py [arguments] file.csp
A distributed run environment similar to mpi-run,
but specifically for executing PyCSP applications.

Copyright (c) 2009 Rune M. Friborg, runef@diku.dk.
See LICENSE.txt for licensing details.

Usage:
  -k <key>, --secret-key <key>    set secret key
  --hostfile <filename>           Set hostfile (default=pycsphost)
"""

### Imports
import os, sys

### Handle commandline arguments
SETTINGS = {'HOSTFILE':'pycsphost'}
if (len(sys.argv) > 1):
    args = sys.argv[1:]
    if ('--help' in args):
        print __doc__
        sys.exit(0)

    for arg in args[:]:
        if ('-k' == arg or '--secret-key' == arg) and len(args) > (args.index(arg)+1):
            SETTINGS['SECRETKEY'] = args[args.index(arg)+1]
            del args[args.index(arg)+1]
            del args[args.index(arg)]

        if ('--hostfile' == arg) and len(args) > (args.index(arg)+1):
            SETTINGS['HOSTFILE'] = args[args.index(arg)+1]
            del args[args.index(arg)+1]
            del args[args.index(arg)]
else:
    print __doc__
    sys.exit(0)


### Read hosts
hosts = []
if os.path.isfile(SETTINGS['HOSTFILE']):
    fp = open(SETTINGS['HOSTFILE'], 'r')
    lines = fp.readlines()
    hosts = map(str.strip, lines)

if len(hosts) == 0:
    print 'No hosts found'
    sys.exit(0)


import subprocess


p = subprocess.Popen(['/usr/bin/env', 'hostname'], stdout=subprocess.PIPE)
stdoutdata, stderrdata = p.communicate()
HOSTNAME = stdoutdata.strip()

def execute(host, cmd, stdin=None, stdout=None, stderr=None):
    if host == 'localhost' or host == HOSTNAME:
        return subprocess.Popen(['/usr/bin/env', 'sh', '-c', "cd "+sys.path[0]+ "; python " + cmd], stdin=stdin, stdout=stdout, stderr=stderr)
    else:
        return subprocess.Popen(['/usr/bin/env', 'ssh', host, "cd "+sys.path[0]+ "; python " + cmd], stdin=stdin, stdout=stdout, stderr=stderr)


p = execute(hosts[0], 'pycsp-server.py', stdout=subprocess.PIPE)
# Wait for 'Running' msg.
p.stdout.readline().strip()
for h in hosts:
    p = execute(h, 'pycsp-daemon.py', stdin=subprocess.PIPE)
    p.stdin.write(SETTINGS['SECRETKEY'] + '\n')
    p.stdin.flush()



