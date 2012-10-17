"""
Copyright (C) 2010 Rune M. Friborg <runef@diku.dk>
"""

import pycsp.net as pycsp

import inspect
import cPickle as pickle
import threading
import random
import time
import types
import os, sys
import subprocess

# local
import support
import migrid as grid


def grid_process(vgrid='ANY', resource=[], disk=1, cputime=60, cpucount=1, nodecount=1, memory=1, inFiles=[], outFiles=[], execFiles=[]):    
    def wrap_process(func):        
        def _call(*args, **kwargs):
            return GridProcess(func, vgrid, resource, disk, cputime, cpucount, nodecount, memory, inFiles, outFiles, execFiles, *args, **kwargs)
        _call.func_name = func.func_name
        return _call
    return wrap_process


class GridProcess(threading.Thread):
    def __init__(self, fn, vgrid, resource, disk, cputime, cpucount, nodecount, memory, inFiles, outFiles, execFiles, *args, **kwargs):

        threading.Thread.__init__(self)

        self.mig = {'vgrid':vgrid,
                    'resource':resource,
                    'disk':disk,
                    'cputime':cputime,
                    'cpucount':cpucount,
                    'nodecount':nodecount,
                    'memory':memory,
                    'inFiles':inFiles,
                    'outFiles':outFiles,
                    'execFiles':execFiles
                    }
        
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        
        # Create unique id
        self.id = str(random.random())+str(time.time())

    def run(self):
        print 'Run Grid Process', str(self.fn)
        # Setup Grid submission
        mRSL_data = self.mig
        #mRSL_data...

        URI = pycsp.Configuration().get(pycsp.NET_SERVER_URI)
        func_name = self.fn.func_name
        srcfile = inspect.getsourcefile(self.fn)
        
        session = support.Session(self.mig, URI, srcfile, func_name, self.args, self.kwargs)
        session.create_package()


        #grid.execute_test(session)
    
        grid_job = grid.Migjob("/usr/bin/env python exec.py " + session.ID,
                    self.mig["vgrid"],
                    session.ID,
                    grid.TEMPDIR)
        grid_job.add_input_file(session.ID + ".tgz")
        grid_job.add_input_file("exec.py")

        grid_job.set_resources("\n".join(self.mig["resource"]))
        grid_job.set_disk(self.mig["disk"])
        grid_job.set_cpu_time(self.mig["cputime"])
        grid_job.set_node_count(self.mig["nodecount"])
        grid_job.set_memory(self.mig["memory"])
                    
        grid.migput(os.path.dirname(__file__) + "/exec.py", "exec.py")
        grid.migput(session.package_file, session.ID + ".tgz")

    
        grid_job.submit()
        grid_job.wait()
                

    # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]
    def __mul__(self, multiplier):
        return [self] + [GridProcess(self.fn, self.mig['vgrid'], self.mig['resource'], self.mig['disk'], self.mig['cputime'], self.mig['cpucount'], self.mig['nodecount'], self.mig['memory'], self.mig['inFiles'], self.mig['outFiles'], self.mig['execFiles'], *self.__mul_channel_ends(self.args), **self.__mul_channel_ends(self.kwargs)) for i in range(multiplier - 1)]

    # syntactic sugar:  2 * Process() == [Process<1>,Process<2>]
    def __rmul__(self, multiplier):
        return [self] + [GridProcess(self.fn, self.mig['vgrid'], self.mig['resource'], self.mig['disk'], self.mig['cputime'], self.mig['cpucount'], self.mig['nodecount'], self.mig['memory'], self.mig['inFiles'], self.mig['outFiles'], self.mig['execFiles'], *self.__mul_channel_ends(self.args), **self.__mul_channel_ends(self.kwargs)) for i in range(multiplier - 1)]

    # Copy lists and dictionaries
    def __mul_channel_ends(self, args):
        if types.ListType == type(args) or types.TupleType == type(args):
            R = []
            for item in args:
                try:                    
                    if type(item.isReader) == types.UnboundMethodType and item.isReader():
                        R.append(item.channel.reader())
                    elif type(item.isWriter) == types.UnboundMethodType and item.isWriter():
                        R.append(item.channel.writer())
                except AttributeError:
                    if item == types.ListType or item == types.DictType or item == types.TupleType:
                        R.append(self.__mul_channel_ends(item))
                    else:
                        R.append(item)

            if types.TupleType == type(args):
                return tuple(R)
            else:
                return R
            
        elif types.DictType == type(args):
            R = {}
            for key in args:
                try:
                    if type(key.isReader) == types.UnboundMethodType and key.isReader():
                        R[key.channel.reader()] = args[key]
                    elif type(key.isWriter) == types.UnboundMethodType and key.isWriter():
                        R[key.channel.writer()] = args[key]
                    elif type(args[key].isReader) == types.UnboundMethodType and args[key].isReader():
                        R[key] = args[key].channel.reader()
                    elif type(args[key].isWriter) == types.UnboundMethodType and args[key].isWriter():
                        R[key] = args[key].channel.writer()
                except AttributeError:
                    if args[key] == types.ListType or args[key] == types.DictType or args[key] == types.TupleType:
                        R[key] = self.__mul_channel_ends(args[key])
                    else:
                        R[key] = args[key]
            return R
        return args


def GridInit():
    if 'run_from_daemon' in sys.argv:
        func_name = sys.argv[-2]
        uri = sys.argv[-1]
        stdindata = ""
        while True:
            l = sys.stdin.readline()
            if not l or l == "ENDOFPICKLE\n":
                break
            stdindata += l

        args, kwargs = pickle.loads(stdindata)

        pycsp.Configuration().set(pycsp.NET_SERVER_URI, uri)

        # Fetch main namespace and execution function
        g = inspect.currentframe().f_back.f_globals
        if g.has_key(func_name):
            print 'Executing', func_name, g[func_name]
            try:
                p = g[func_name](*args, **kwargs)
                p.fn(*args, **kwargs)
            except pycsp.ChannelPoisonException, e:
                # look for channels and channel ends
                __check_poison(args)
                __check_poison(kwargs.values())
            except pycsp.ChannelRetireException, e:
                # look for channel ends
                __check_retire(args)
                __check_retire(kwargs.values())

        sys.exit(0)


def __check_poison(args):
    for arg in args:
        try:
            if types.ListType == type(arg) or types.TupleType == type(arg):
                __check_poison(arg)
            elif types.DictType == type(arg):
                __check_poison(arg.keys())
                __check_poison(arg.values())
            elif type(arg.poison) == types.UnboundMethodType:
                arg.poison()
        except AttributeError:
            pass

def __check_retire(args):
    for arg in args:
        try:
            if types.ListType == type(arg) or types.TupleType == type(arg):
                __check_retire(arg)
            elif types.DictType == type(arg):
                __check_retire(arg.keys())
                __check_retire(arg.values())
            elif type(arg.retire) == types.UnboundMethodType:
                # Ignore if try to retire an already retired channel end.
                try:
                    arg.retire()
                except ChannelRetireException:
                    pass
        except AttributeError:
            pass

