"""
Stochastic Minimum Search

"""
from pycsp_import import *
from pycsp import *
import pylab

@process
def gmin(fin,chout):
  delta=0.01
  try:
    f = fin()
    while True:
      x,y=pylab.random(),pylab.random()
      min=eval(f)
      change=min+10
      i = 0
      while change<>min and i<10000:
        min=pylab.minimum(change,min)
        x+=delta
        if not eval(f)<min: x-=delta
        x-=delta
        if not eval(f)<min: x+=delta
        y+=delta
        if not eval(f)<min: y-=delta
        y-=delta
        if not eval(f)<min: y+=delta
        change=eval(f)
      if change == min:
        chout(min)
      g, msg = Alternation([
          {fin:None},
          {Skip():None}
          ]).select()
      if g == fin:
        print "Updated f to %s" % (f)
        f = msg

  except:
    pass


@process 
def master(kbd, scr, workers_i, workers_o):
  log = []
  while True:
    Alternation([{
                 kbd:"workers_o(__channel_input)",
                 workers_i:"""
log.append(__channel_input)
log.sort()
scr(log[0])
"""
                 }]).execute()

@process
def userin(kbd):
  while True:
    str_input = raw_input('CMD >')
    if str_input.strip() == 'f':
      kbd(raw_input('Enter new f:'))
    elif str_input.strip() == 'q':
      poison(kbd)

@process
def userout(scr):
  while True:
    print scr()

kbd, scr, updatef, workers = Channel(), Channel(), Channel(), Channel()
N=10

#f= 'x**2+y**2-pylab.cos(18*x)-pylab.cos(18*y)+2'

Parallel(userin(OUT(kbd)),
         userout(IN(scr)),
         master(IN(kbd), OUT(scr), IN(workers), OUT(updatef)),
         [gmin(IN(updatef), OUT(workers)) for i in range(N)]
        )

