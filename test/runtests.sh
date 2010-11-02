#!/bin/sh

PYTHON=python

$PYTHON autotest.py
$PYTHON buffertest.py 
$PYTHON commtest.py 
$PYTHON guardtest.py 
$PYTHON iotest.py 
$PYTHON poisontest.py 
$PYTHON selecttest.py 
