#!/bin/sh

PYCSP_PORT=10011 python DistCommstimeConsumer.py &
PYCSP_PORT=10012 python DistCommstimeDelta2.py &
PYCSP_PORT=10013 python DistCommstimePrefix.py &
PYCSP_PORT=10014 python DistCommstimeSuccessor.py

