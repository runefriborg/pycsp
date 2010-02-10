#!/usr/bin/env python
# -*- coding: latin-1 -*-
# 
# see http://docs.python.org/dist/dist.html
# 
"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from setuptools import setup

setup(name='pycsp',
      version='0.6.2',
      description='PyCSP - Python CSP Library',
      long_description="""
The PyCSP library has been completely rewritten.

There is no backwards compatibility with versions prior to 0.5.0.

For now please look at the examples for documentation on how to use the library.""",
      author='John Markus Bjørndalen',
      author_email='jmb@cs.uit.no',
      url='http://code.google.com/p/pycsp/',
      license='MIT',
      packages=['pycsp', 'pycsp.threads', 'pycsp.processes', 'pycsp.greenlets', 'pycsp.net'],
      platforms=['any'],
      )
