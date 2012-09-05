from pycsp_import import *

@process
def producer(job_out):
  for i in range(-10, 0):
    job_out(i)

  job_out("replay")
  
  for i in range(0, 11):
    job_out(i)

  while True:
    job_out("retire")

@process
def worker(job_in, job_out):
  while True:
    x = job_in()
    job_out(x * 2)

@process
def replayer(job_in, job_out, replay):
  jobs = []
  while True:
    x = job_in()

    if x == "delete":
      jobs = []
    elif x == "replay":
      for j in jobs:
        replay(j)
    elif x == "retire":
      raise ChannelRetireException
    else:
      jobs.append(x)
      job_out(x)

@process
def consumer(job_in):
  while True:
    print job_in()

c = Channel()
c1,c2,c3 = Channel(),Channel(),Channel()
d = Channel()

Parallel(
  producer(-c),
  replayer(+c, -c1, -c),
  replayer(+c, -c2, -c),
  replayer(+c, -c3, -c),
  worker(+c1, -d),
  worker(+c2, -d),
  worker(+c3, -d),
  consumer(+d)
)