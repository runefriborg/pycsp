#!/usr/bin/env python

from pycsp import daemonNet
import sys
import time


daemonNet.Configuration().set(daemonNet.NET_SERVER_ID, 'daemonNet')

anyChannel = daemonNet.Channel('AnyDaemon')
anyChannel.poison()

serverChannel = daemonNet.Channel('Server')
serverChannel.poison()




