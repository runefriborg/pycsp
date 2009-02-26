#!/usr/bin/env python
# -*- coding: latin-1 -*-
# 
# see http://docs.python.org/dist/dist.html
# 
from distutils.core import setup


setup(name='pycsp',
      version='0.3.0',
      description='PyCSP - Python CSP Library',
      author='John Markus Bjørndalen',
      author_email='jmb@cs.uit.no',
      url='http://www.cs.uit.no/~johnm/code/PyCSP/',
      license='MIT',
      packages=['pycsp', 'pycsp.net', 'pycsp.plugNplay'],
      platforms=['any'],
      )
