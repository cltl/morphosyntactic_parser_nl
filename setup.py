#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='alpinonaf',
      version='0.3',
      description='NAF Wrapper around the Alpino parser',
      author='Ruben Izquierdo',
      author_email='rubensanvi@gmail.com',
      url='https://github.com/cltl/alpinonaf',
      packages=['alpinonaf'],
      install_requires=['KafNafParserPy', 'requests', 'six']
      )
