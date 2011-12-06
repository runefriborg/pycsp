#!/bin/sh

python DistCommsTimeConsumer.py &
python DistCommsTimeDelta2.py &
python DistCommsTimePrefix.py &
python DistCommsTimeSuccessor.py

