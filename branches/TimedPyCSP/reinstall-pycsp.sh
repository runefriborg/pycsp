#!/bin/bash

sudo apt-get remove pycsp
sudo rm -rf /usr/share/pyshared/pycsp/
make -C /home/shamran/pycsp/branches/TimedPyCSP builddeb
sudo gdebi /home/shamran/pycsp/branches/pycsp_0.6.2-0.3_all.deb 
