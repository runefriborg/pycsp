#!/bin/sh

python DistCommsTimePrefix.py &
sleep 5
python DistCommsTimeConsumer.py &
python DistCommsTimeDelta2.py &
python DistCommsTimeSuccessor.py

