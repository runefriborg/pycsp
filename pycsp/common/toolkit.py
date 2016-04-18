"""
Toolkit module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""


from pycsp.common.six import string_types
import pycsp.current as pycsp

if pycsp.trace:
    from pycsp.common import trace as pycsp

import subprocess
import types


def which(cmd):
    P = subprocess.Popen(args=('which', cmd), stdin=None, stdout=subprocess.PIPE)
    (stdout, _) = P.communicate()
    return stdout.strip()


@pycsp.process
def file_r(cout, file, retire_on_eof=True, sep="\n"):

    if isinstance(file, string_types):
        file = open(file, 'r')
        
    try:
        buf = []
        line = file.readline()
        while (line):
            buf.append(line)
            if buf[-1].find(sep) > -1:
                cout(buf)
                buf = []
            line = file.readline()
        if buf:
            cout(buf)
    except:
        pass

    file.close()
    if retire_on_eof:
        pycsp.retire(cout)


@pycsp.process
def file_w(cin, file):
    
    if isinstance(file, string_types):
        file = open(file, 'w')

    try:
        while True:
            data = cin()
            if type(data) == list:
                file.write(''.join(data))
            else:
                file.write(data)
            file.flush()
    except:
        file.close()


@pycsp.process
def runner(cin):
    while True:
        command, stdinChEnd, stdoutChEnd, stderrChEnd = cin()

        pycsp.Sequence(
            execute(command, stdinChEnd, stdoutChEnd, stderrChEnd)
            )

        
@pycsp.process
def execute(command, stdinChEnd=None, stdoutChEnd=None, stderrChEnd=None, retire_on_eof=True):

        stdin, stdout, stderr = [None]*3
        if stdinChEnd: stdin = subprocess.PIPE
        if stdoutChEnd: stdout = subprocess.PIPE
        if stderrChEnd: stderr = subprocess.PIPE

        P = subprocess.Popen(args=command,
                             stdin=stdin,
                             stdout=stdout,
                             stderr=stderr)
            
        @pycsp.choice
        def handle_stdin(channel_input, stdin):
            stdin.write(channel_input)
            stdin.flush()

        @pycsp.choice
        def forwarder(channel_input, cout):
            cout(channel_input)
        

        altList = []
        if stdinChEnd:
            altList.append((stdinChEnd, handle_stdin(stdin=P.stdin)))

        if stdoutChEnd:
            C1 = pycsp.Channel()
            C1in = C1.reader()
            pycsp.Spawn(file_r(C1.writer(), P.stdout))
            altList.append((C1in, forwarder(cout=stdoutChEnd)))

        if stderrChEnd:
            C2 = pycsp.Channel()
            C2in = C2.reader()
            pycsp.Spawn(file_r(C2.writer(), P.stderr))
            altList.append((C2in, forwarder(cout=stderrChEnd)))

        if altList:
            alt = pycsp.Alternation(altList)

            try:
                while True:
                    alt.execute()
                
            except pycsp.ChannelRetireException:
                # stdout has reached eof
                if stdoutChEnd:
                    pycsp.retire(C1in)
                if stderrChEnd:
                    pycsp.retire(C2in)

                if retire_on_eof:
                    if stdoutChEnd:
                        pycsp.retire(stdoutChEnd)
                    if stderrChEnd:
                        pycsp.retire(stderrChEnd)
                    
        else:
            
            P.wait()

