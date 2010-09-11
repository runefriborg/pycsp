"""
Copyright (C) 2010 Rune M. Friborg <runef@diku.dk>
"""
import uuid
import os, shutil
import cPickle as pickle
import subprocess

TEMP_DIR="/tmp"

class Session:
    def __init__(self, grid_settings, URI, srcfile, fn, args, kwargs):
        self.ID = "pycsp_grid_" + str(uuid.uuid4())
        self.grid_settings = grid_settings
        self.URI = URI
        self.srcfile = srcfile
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        
    def create_package(self):
        self.package_file = TEMP_DIR + "/" + self.ID + ".tgz"

        PACKAGE_DIR = TEMP_DIR + "/" + self.ID
        os.mkdir(PACKAGE_DIR)
        
        # copy pycsp
        pycsp_loc = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        shutil.copytree(pycsp_loc, PACKAGE_DIR + "/" + 'pycsp', symlinks=True)

        # copy input files
        shutil.copy(self.srcfile, PACKAGE_DIR + "/" + self.srcfile)
        for f in self.grid_settings['inFiles']:
            shutil.copy(f, PACKAGE_DIR + "/" + f)

        # create arg file
        pickled_args = pickle.dumps((self.args, self.kwargs), protocol=pickle.HIGHEST_PROTOCOL)

        f = open(PACKAGE_DIR + "/" + self.ID + ".data", "w")
        pickle.dump((self.URI, self.fn, self.srcfile, pickled_args), f , protocol=pickle.HIGHEST_PROTOCOL)
        f.close()

        # pack
        subprocess.Popen(["tar", "-czf", self.package_file, "-C", TEMP_DIR, self.ID]).wait()


        




