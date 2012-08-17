from pycsp_import import *

@process(fail_type=RETIRELIKE, print_error=True)
def producer(cout, dout, job_start, job_end):
    try:
      for i in range(job_start, job_end):
        cout(i)
    except ChannelRetireLikeFailstopException:
      for i in range(i, job_end):
        dout(i)

@process(fail_type=RETIRELIKE, print_error=True)
def failer(cin, fout):
  while True:
    x = cin()
    fout(x*2)
    raise Exception("failed hardware")

@process(fail_type=RETIRELIKE, print_error=True)
def worker(din, fout):
  while True:
    x = din()
    fout(x*2)

@process(fail_type=RETIRELIKE, print_error=True)
def consumer(finish):
  while True:
    try:
      x = finish()
      print x
    except ChannelRetireLikeFailstopException:
      pass

c = Channel()
d = Channel()
f = Channel()
start = Channel()

Parallel(
  producer(-c, -d, -10, 10),
  failer(+c, -f),
  worker(+d, -f),
  consumer(+f)
)