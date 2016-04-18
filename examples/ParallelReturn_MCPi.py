"""
Copyright (c) 2009 Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *
from random import random
from functools import reduce

if version[3] == "greenlets":
   multiprocess = process

@process
def work1(cnt):
   sum = reduce(lambda x,y: x+(random()**2+random()**2<1.0), list(range(cnt)))
   return (4.0*sum)/cnt  #Return result

@multiprocess
def work2(cnt):
   sum = reduce(lambda x,y: x+(random()**2+random()**2<1.0), list(range(cnt)))
   return (4.0*sum)/cnt  #Return result

cnt = 100000
P = 20

def sum(a,b):
   return a+b

if __name__ == '__main__':
   L = Parallel((P/2) * work1(cnt), (P/2) * work2(cnt))
   print("Processes return " + str(L))
   all = reduce(sum, L)
   print(("Result: %f" % (all/P)))

shutdown()
