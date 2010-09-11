"""
Copyright (C) 2010 Rune M. Friborg <runef@diku.dk>
"""
import os, shutil, subprocess

TEMPDIR = "/tmp"

def upload(session):
    exec_file = os.path.dirname(__file__) + "/exec.py"
    print session.package_file
    print exec_file
    
    shutil.copy(exec_file, TEMPDIR + "/exec.py")

    # New exec that are moved to EXEC section of mRSL
    cmd = ['/usr/bin/env', 'python', 'exec.py', session.ID]
    p = subprocess.Popen(cmd, cwd=TEMPDIR)
    p.wait()




















#################################################
# MiG commands
#################################################
