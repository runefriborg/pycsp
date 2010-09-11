"""
Copyright (C) 2010 Rune M. Friborg <runef@diku.dk>
"""
import subprocess
import sys, os
import cPickle as pickle

session_ID = sys.argv[1]
package_file = session_ID + ".tgz"

# Test for file
if not os.path.exists(package_file):
    print 'Failed finding file', package_file
    sys.exit(0)

# Unpacks into a session_ID folder.
subprocess.Popen(["tar", "-xzf", package_file]).wait()

# Change dir to session folder
os.chdir(session_ID)

# load values
f = open(session_ID + ".data", "r")
URI, func_name, srcfile, pickled_args = pickle.load(f)
f.close()


# Exec
cmd = ['/usr/bin/env', 'python', srcfile, 'run_from_daemon', func_name, str(URI)]
print cmd
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
p.stdin.write(pickled_args+"\n")
p.stdin.write("ENDOFPICKLE\n")
p.stdin.close()                
p.wait()


