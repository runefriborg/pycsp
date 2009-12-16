 #!/bin/bash
rm /home/shamran/pycsp/branches/TimedPyCSP/pycsp/simulation/*.orig 2>/dev/null
rm /home/shamran/pycsp/branches/TimedPyCSP/pycsp/greenlets/*.orig 2>/dev/null

rm /home/shamran/pycsp/branches/TimedPyCSP/pycsp/simulation/*~ 2>/dev/null
rm /home/shamran/pycsp/branches/TimedPyCSP/pycsp/greenlets/*~ 2>/dev/null

rm /home/shamran/pycsp/branches/TimedPyCSP/pycsp/simulation/*.pyc 2>/dev/null
rm /home/shamran/pycsp/branches/TimedPyCSP/pycsp/greenlets/*.pyc 2>/dev/null

sudo cp -R /home/shamran/pycsp/branches/TimedPyCSP/pycsp/* /usr/share/pyshared/pycsp/
