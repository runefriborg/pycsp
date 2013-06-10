"""
Functions for sending the result through stdout from the process. Will catch stdout and output it after
the pickled return value.

Usage:
  real_stdout = save_stdout()

  # run code (with output to stdout)

  output = output_and_restore_stdout(value, real_stdout)
  
  (from parent process)
  value = retrive_value_from_stream(real_stdout)

  Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

import const
import sys

try:
    from cStringIO import StringIO
except:
    from io import StringIO

try:
    from cPickle import pickle
except:
    import pickle

def save_stdout():
    real_stream = sys.stdout
    sys.stdout = StringIO()
    return real_stream


def output_and_restore_stdout(value, real_stream):
    # Write pickled data to stdout
    pickle.dump(value, real_stream, protocol=const.PICKLE_PROTOCOL)
    
    # Restore stdout
    stream = sys.stdout
    sys.stdout = real_stream
    
    # Output saved stdout data to stdout
    sys.stdout.write((stream.getvalue()))
    stream.close()


def retrieve_value_from_stream(inputstream):
    try:
        return pickle.load(inputstream)
    except:
        return None

