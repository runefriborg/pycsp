from pycsp.dist import *
import math, random

@process
def gmin(chin,chout, max_loops=500):
  f=chin()
  print "F is "+ f
  delta=0.01
  try:
    for loop in xrange(max_loops):
      x,y=random.random(),random.random()
      min=eval(f)
      change=min+10
      while change<>min:
        if change < min:
          min = change
        x+=delta
        if not eval(f)<min: x-=delta
        x-=delta
        if not eval(f)<min: x+=delta
        y+=delta
        if not eval(f)<min: y-=delta
        y-=delta
        if not eval(f)<min: y+=delta
        change=eval(f)
      chout(min)
    poison(chin, chout)
  except:
    pass

@process 
def master(filter, workers_o, workers_i, n, f):
  for i in range(n):
    workers_o(f)

  while True:
    filter(workers_i())

  if False:
    Alternation([{
                 kbd:None,
                 workers_i:'filter(__channel_input)'
                 }]).execute()



@process
def userout(scr):
  while True:
    print scr()

@process
def filter_minimum(cin, cout):
  res=cin()
  cout(res)
  while True:
    cand=cin()
    if cand<res:
      res=cand
      cout(res)
  

Init(secretKey='Fisk')

kbd=Channel()
scr=Channel()
filter = Channel()
to_worker=Channel()
from_worker=Channel()
N=5

Parallel(userout(IN(scr)),
         filter_minimum(IN(filter), OUT(scr)),
         master(OUT(filter), OUT(to_worker), IN(from_worker), N, f='x**2+y**2-math.cos(18*x)-math.cos(18*y)+2'),
         [gmin(IN(to_worker), OUT(from_worker)) for i in range(N)]
        )

#print gmin('x**2+y**2-pylab.cos(18*x)-pylab.cos(18*y)+2')

