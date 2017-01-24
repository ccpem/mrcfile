# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

from setuptools import setup

from mrcfile.version import __version__

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='mrcfile',
    version=__version__,
    packages=['mrcfile'],
    install_requires=['numpy >= 1.12.0'],
    
    test_suite='tests',
    
    author='Colin Palmer',
    author_email='colin.palmer@stfc.ac.uk',
    description='MRC file I/O library',
    long_description=readme(),
    license='BSD',
    url='https://github.com/ccpem/mrcfile',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
