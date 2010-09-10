"""
Copyright (C) 2010 Rune M. Friborg <runef@diku.dk>
"""
import uuid
import os, shutil

TEMP_DIR="/tmp"

class Session:
    def Session(self, grid_settings, URI, srcfile, fn, args, kwargs):
        self.ID = uuid.uuid4()
        self.grid_settings = grid_settings
        self.URI = URI
        self.srcfile = srcfile
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        
    def create_package(self):
        self.package_file = self.ID + ".tgz"

        curdir = os.path.realpath(os.curdir)
        os.chdir(TEMP_DIR)
        
        os.mkdir(self.ID)
        
        # copy pycsp
        pycsp_loc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        shutil.copytree(pycsp_loc, self.ID + "/")

        # copy input files
        shutil.copy(curdir + "/" + self.srcfile, self.ID + "/")
        for f in self.grid_settings['inFiles']:
            shutil.copy(curdir + "/" + f, self.ID + "/")
        
        # pack
        subprocess.Popen(["tar", "-xcf", package_file, self.ID]).wait()


# Change dir to session folder
os.chdir(session_ID)

# load values
URI, func_name, srcfile, pickled_args = pickle.load(session_ID + ".data")

# Exec
cmd = ['/usr/bin/env', 'python', srcfile, 'run_from_daemon', func_name, str(URI)]
print cmd
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
p.stdin.write(pickled_args+"\n")
p.stdin.write("ENDOFPICKLE\n")
p.stdin.close()                
p.wait()







