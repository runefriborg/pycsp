from pycsp_import import *
from random import randint

reruns = 0
fail = True

def fail_half():
  global fail
  fail = not fail
  if fail:
    return 0
  else:
    return 1

@process(fail_type=CHECKPOINT)
def A(cout, cin, fout):
  while True:
    cout("Ping")
    fout(cin())     
    
@process(fail_type=CHECKPOINT, print_error=False, retires=-1, fail_type_after_retires=FAILSTOP)
def B(cout, cin, fout):
  global reruns
  reruns += 1

  while True:
    x = cin()    
    cout("Pong")  # This line
    1/fail_half() # fails half
    fout(x)       # the time
    
@process(fail_type=CHECKPOINT)
def C(fin, num):
  i = load(i = 1)
  for i in range(i, num):
    x = fin()
    print i, x
  poison(fin)

c = Channel() 
f = Channel()

Parallel(
  A(-c, +c, -f),
  B(-c, +c, -f),
  C(+f, 100)
)

print "\nreruns:", reruns