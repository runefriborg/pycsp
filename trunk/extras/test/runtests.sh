#!/bin/sh

PYTHON=python
IMPL=$1

$PYTHON autotest.py $IMPL
$PYTHON buffertest.py $IMPL
$PYTHON commtest.py $IMPL
$PYTHON guardtest.py $IMPL
$PYTHON iotest.py $IMPL
$PYTHON poisontest.py $IMPL
$PYTHON selecttest.py $IMPL
