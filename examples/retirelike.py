from pycsp_import import *
from random import randint

@process
def A(cout, cin, fout):
  while True:
    print "using cout in A"
    cout("Ping")
    print "using fout and cin in A"
    fout(cin())      

@process
def B(cout, cin, fout):
  while True:
    print "using cin in B"
    x = cin()
    print "using cout in B"
    cout("Pong")
    if randint(0, 1):  # This line fails 
      print "retire"
      retire(cout)
      retire(fout)
      retire(cin)
    else:
      print "using fout in B"
      fout(x)         # half the time

@process
def C(fin, num):
  for i in range(num):
    print "using fin in C", i
    x = fin()
    print i, x

c = Channel()
f = Channel()

Parallel(
  A(-c, +c, -f),
  B(-c, +c, -f),
  C(+f, 10)
)