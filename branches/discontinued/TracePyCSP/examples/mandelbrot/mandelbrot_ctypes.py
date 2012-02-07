from pycsp_import import *
from numpy import *
import sys

from ctypes import *
mandelbrot=CDLL('mandelbrot_kernel.dylib')
#mandelbrot=CDLL('mandelbrot_kernel.so')

args = sys.argv
workers = int(args[2])
jobcount = int(args[3])
width = int(args[4])
height = int(args[5])

import time
def init_time_record():
    return {'total':0,'diff':time.time(),'calls':0}

def t1(record):
    record['diff'] = time.time()
    record['calls'] += 1

def t2(record):
    record['total'] += time.time() - record['diff']
    record['diff'] = -9999

def compute(u, h_step, w_step, h_start, w_start, h, w, maxit):
    mandelbrot.compute(u.ctypes.data_as(c_void_p),
                       c_double(h_step),
                       c_double(w_step),
                       c_double(h_start),
                       c_double(w_start),
                       c_int(h),
                       c_int(w),
                       c_int(maxit))
    

@process
def worker(cin, cout, maxit = 5000):
    time_rec = init_time_record()
    try:
        while True:
            (id, w_start, w_step, w, h_start, h_step, h) = cin()
            t1(time_rec)

            u=zeros((h,w), dtype=uint16)
            compute(u, h_step, w_step, h_start, w_start, h, w, maxit)

            t2(time_rec)
            cout((id, u))
    except ChannelRetireException:
        sys.stdout.write('  Worker: %d calls, %fs\n' % (time_rec['calls'],time_rec['total']))


@process
def manager(workerOut, workerIn, w, h, jobcount):
    time_rec = init_time_record()

    #xmin = -2.0
    #xmax = 0.8
    #ymin = -1.4
    #ymax = 1.4

    xmin = -1.6744096758873175
    xmax = -1.6744096714940624
    ymin = 0.00004716419197284976
    ymax = 0.000047167062611931696

    w_step = (xmax-xmin)/w
    h_step = (ymax-ymin)/h
    w_start = xmin
    h_start = ymin

    job_h = h/jobcount

    # Generate jobs
    # Tuple: (job_id, w_start, w_step, width, h_start(job), h_step, job_h)
    jobs = []
    for job_id in xrange(jobcount):
        jobs.append(
            (job_id,
            w_start, w_step, w,
            h_start + h_step * (job_id * job_h), h_step, job_h)
            )

    if job_h*jobcount < h:
        last_h = h - job_h*jobcount
        jobs.append(
            (jobcount,
            w_start, w_step, w,
            h_start + h_step*(jobcount*job_h), h_step, last_h))

    jobcount = len(jobs)

    # Deliver and receive
    results = [None for i in range(jobcount)]
    received = 0
    while jobs or received < jobcount:
        t2(time_rec)
        if jobs:
            guard, msg = Alternation([
                        (workerIn, None),
                        (workerOut, jobs[-1], "jobs.pop(-1)")
                        ]).execute()
                                     
        else:
            guard = workerIn
            msg = guard()
        t1(time_rec)

        if guard == workerIn:
            job_id, result = msg
            received += 1
            results[job_id] = result        

    # Produce result                
    u = concatenate(results, axis=0)
    u = concatenate(u, axis=0)
    u = uint16(u / (u.max()/255.0))

    import png

    img = png.Writer(w, h, greyscale=1)
    img.write_array(open("out.png", 'w'), u)
    sys.stdout.write('  Manager: %fs\n' % (time_rec['total']))
    retire(workerOut, workerIn)



if __name__ == '__main__':

    print 'PyCSP mandelbrot'
    print ' workers  :', workers
    print ' jobcount :',jobcount
    print ' size     :', (width, height)

    rec_time_t = init_time_record()

    jobChannel = Channel()
    resultChannel = Channel()

    Parallel(manager(jobChannel.writer(), resultChannel.reader(), width, height, jobcount),
             [worker(jobChannel.reader(), resultChannel.writer()) for i in range(workers)])

    t2(rec_time_t)
    sys.stdout.write(' *** Total: %f\n' % (rec_time_t['total']))
    sys.stdout.write(' NB: includes channel create, job create and process startup/exit times\n')
    sys.stdout.write(' @%s\n' % (repr((jobcount, width, height, workers, rec_time_t['total'], "PyCSP"))))
