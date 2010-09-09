"""Version: Mcstas wrapper 1.0
Copyright (C) 2009 Rune M. Friborg <runef@diku.dk>

Usage: mcrun-pycsp.py [options ...] <ncount> <file.instr>

Options:
  -maxncount <int>  max neutron count per job
  -workers <int>    number of workers

  -i                print instrument info and quit
  --help            print this info
"""

from pycsp_import import *
from pycsp.common.trace import *

from pycsp import threads as pycsplocal
 


import sys, types
import time
import random
import math

import subprocess
import types

TraceInit('mcrun-pycsp.trace')

def which(cmd):
    P = subprocess.Popen(args=('which', cmd), stdin=None, stdout=subprocess.PIPE)
    (stdout, _) = P.communicate()
    return stdout.strip()


@pycsplocal.process
def file_r(cout, file, retire_on_eof=True, sep="\n"):
    if types.StringType == type(file):
        file = open(file, 'r')
    
    if types.FileType == type(file):
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
            pycsplocal.retire(cout)


@pycsplocal.process
def file_w(cin, file):
    if types.StringType == type(file):
        file = open(file, 'w')

    if types.FileType == type(file):
        try:
            while True:
                data = cin()
                if type(data) == types.ListType:
                    file.write(''.join(data))
                else:
                    file.write(data)
                file.flush()
        except:
            file.close()


@process
def runner(cin):
    while True:
        command, stdinChEnd, stdoutChEnd, stderrChEnd = cin()

        Parallel(
            execute(command, stdinChEnd, stdoutChEnd, stderrChEnd)
            )

        
@process
def execute(command, stdinChEnd=None, stdoutChEnd=None, stderrChEnd=None, retire_on_eof=True):

        TraceMsg(command[0])

        stdin, stdout, stderr = [None]*3
        if stdinChEnd: stdin = subprocess.PIPE
        if stdoutChEnd: stdout = subprocess.PIPE
        if stderrChEnd: stderr = subprocess.PIPE

        P = subprocess.Popen(args=command,
                             stdin=stdin,
                             stdout=stdout,
                             stderr=stderr)
            
        @choice
        def handle_stdin(channel_input, stdin):
            stdin.write(channel_input)
            stdin.flush()

        @choice
        def forwarder(channel_input, cout):
            cout(channel_input)
        

        altList = []
        if stdinChEnd:
            altList.append((stdinChEnd, handle_stdin(stdin=P.stdin)))

        if stdoutChEnd:
            C1 = Channel()
            C1in = C1.reader()
            pycsplocal.Spawn(file_r(C1.writer(), P.stdout))
            altList.append((C1in, forwarder(cout=stdoutChEnd)))

        if stderrChEnd:
            C2 = Channel()
            C2in = C2.reader()
            pycsplocal.Spawn(file_r(C2.writer(), P.stderr))
            altList.append((C2in, forwarder(cout=stderrChEnd)))

        if altList:
            alt = Alternation(altList)

            try:
                while True:
                    alt.execute()
                
            except ChannelRetireException:
                # stdout has reached eof
                if stdoutChEnd:
                    retire(C1in)
                if stderrChEnd:
                    retire(C2in)

                if retire_on_eof:
                    if stdoutChEnd:
                        retire(stdoutChEnd)
                    if stderrChEnd:
                        retire(stderrChEnd)
                    
        else:
            
            P.wait()




MCRUN = which('mcrun')
MCSTAS = which('mcstas')
MCFORMAT = which('mcformat')
GCC = which('mpicc')



@process
def screen(cin):
    while True:
        print cin()

@process
def mcstas(instr_in, c_out, screenC):
    while True:
        instr_file = instr_in()
        c_file = instr_file[:instr_file.index('.')] + ".c"

        cmd=(MCSTAS, '-t', '-o', c_file, instr_file)
        #screenC(str(cmd))
        Parallel(
            execute(cmd, stdoutChEnd=screenC, retire_on_eof=False)
            )

        c_out(c_file)


@process
def compile(exec_out, c_in, screenC):
    while True:
        c_file = c_in()
        exec_file = c_file[:c_file.index('.')] + ".out"

        #cmd=(GCC, '-g' ,'-lm', '-O2', '-o', exec_file, c_file)
        #screenC(str(cmd))
        #Parallel(
        #    execute(cmd, stdoutChEnd=screenC, retire_on_eof=False)
        #    )

        exec_out(exec_file)


@process
def paramspace(job_out, config):

    # Calculate permutations recursively
    def permutations(index, items, current = []):
        if index < len(items):
            key, conf = items[index]
            if type(conf) == tuple and len(conf) == 3 :                
                start, stop, step = conf
                val = start
                while (val <= stop):
                    permutations(index + 1, items, current + [key + '=' + str(val)])
                    val += step
            else:
                permutations(index + 1, items, current + [key + '=' + str(conf)])
        else:
            job_out(current)
        
    permutations(0, config.items())
    retire(job_out)

@process
def divide_jobs(job_in, job_out, ncount, maxncount):
    jobs = 1
    job_ncount = ncount
    job_rest = 0

    if ncount > maxncount:
        jobs = int(math.ceil(ncount / maxncount))
        job_ncount = maxncount
        job_rest = ncount - (job_ncount * jobs)
        
    while True:
        params = job_in()
        for i in xrange(jobs):
            job_out((job_ncount, params))
        if job_rest:
            job_out((job_rest, params))
        
@process
def simulate(job_in, result_out, screenC, exec_file):
    while True:
        ncount, params = job_in()
        data_dir = exec_file + "-data-" + str(random.random())+str(time.time())

        cmd=tuple(['./' + exec_file, 
             '--seed=' + str(int(random.random()*10000000)+1),
             '--ncount=' + str(ncount),
             '--dir=' + data_dir] + params)
             
        screenC(str(cmd))
        Parallel(
            execute(cmd, stdoutChEnd=screenC, retire_on_eof=False)
            )

        result_out(data_dir)
        

@process
def merge(result_in, exec_file=''):
    while True:
        data_dir = result_in()
        merged_dir = exec_file + "-merged"

        cmd=(MCFORMAT,
             '--merge', '--force', '--dir=' + merged_dir, data_dir)

        #print cmd
        Parallel(
            execute(cmd)
            )
        

@process
def orchestrate_network(instr_out, exec_in, screen_chan, params):

    if '--help' in params or len(params) < 2:
        print __doc__
        retire(instr_out)
        return

    INSTRUMENT = params[-1]
    params.pop()
    instr_out(INSTRUMENT)

    NCOUNT = int(eval(params[-1]))
    params.pop()

    MAXNCOUNT = NCOUNT
    if '-maxncount' in params:
        i = params.index('-maxncount')
        MAXNCOUNT = int(eval(params[i+1]))
        params.pop(i)
        params.pop(i)

    WORKERS = int(NCOUNT / MAXNCOUNT)
    if '-workers' in params:
        i = params.index('-workers')
        WORKERS = int(params[i+1])
        params.pop(i)
        params.pop(i)
    if WORKERS < 1:
        WORKERS = 1

    PRINT_INSTRUMENT_INFO = False
    if '-i' in params:
        PRINT_INSTRUMENT_INFO = True
        
    exec_file = exec_in()

    # Get default parameters from instrument
    instrument_info = Channel()
    Spawn(
        execute(('./' + exec_file, '-i'), stdoutChEnd= -instrument_info)
        )

    config = {}

    try:
        cin = +instrument_info
        while(True):
            line = cin()[0]
            if PRINT_INSTRUMENT_INFO:
                print line,

            line = line.strip()
            if line.find('Param: ') >= 0:
                equal_pos = line.find('=')
                config[line[7:equal_pos]] = eval(line[equal_pos+1:])
    except ChannelRetireException:
        pass

    if PRINT_INSTRUMENT_INFO:
        retire(instr_out)
        return

    # Parse parameters from args
    for conf in config:
        if conf in params:
            i = params.index(conf)
            try:
                val = eval(params[i+1])
            except IndexError:
                print 'Error: Need value / (start, stop, step) for %s' % conf

            config[conf] = val

    # Remove None values
    for conf in config.keys():
        if config[conf] == None:
            del config[conf]

    # Compute across parameter space
    B = [Channel(name='B_'+str(i)) for i in range(3)]
    Parallel(
        paramspace(-B[0], config),
        divide_jobs(+B[0], -B[2], NCOUNT, MAXNCOUNT),
        [simulate(   +B[2], -B[1], -screen_chan, exec_file) for i in range(WORKERS)],
        merge(             +B[1], exec_file)
        )

    retire(instr_out)



# C = Channel() * 5    
C = [Channel() for i in range(5)]


Parallel(
    screen(  +C[0]),
    orchestrate_network(   -C[1], +C[2], C[0], sys.argv[1:]),
    mcstas(  +C[1], -C[4], -C[0]),
    compile( -C[2], +C[4], -C[0])
    )



TraceQuit()
