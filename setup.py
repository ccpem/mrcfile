# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

import os.path
from setuptools import setup

base_url = 'https://github.com/ccpem/mrcfile'

def version():
    """Get the version number without importing the mrcfile package."""
    namespace = {}
    with open(os.path.join('mrcfile', 'version.py')) as f:
        exec(f.read(), namespace)
    return namespace['__version__']

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='mrcfile',
    version=version(),
    packages=['mrcfile'],
    install_requires=['numpy >= 1.12.0'],
    
    test_suite='tests',
    
    entry_points = {
        'console_scripts': [
            'mrcfile-header = mrcfile.command_line:print_headers',
            'mrcfile-validate = mrcfile.validator:main'
        ],
    },
    
    author='Colin Palmer',
    author_email='colin.palmer@stfc.ac.uk',
    description='MRC file I/O library',
    long_description=readme(),
    license='BSD',
    url=base_url,
    download_url='{0}/releases'.format(base_url),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
