#!/bin/sh

python DistCommstimeConsumer.py &
python DistCommstimeDelta2.py &
python DistCommstimePrefix.py &
python DistCommstimeSuccessor.py

