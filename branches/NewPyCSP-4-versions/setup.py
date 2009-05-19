#!/usr/bin/env python
# -*- coding: latin-1 -*-
# 
# see http://docs.python.org/dist/dist.html
# 
from setuptools import setup

setup(name='pycsp',
      version='0.6.0',
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
