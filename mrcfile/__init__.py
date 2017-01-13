# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
mrcfile
=======

A pure Python implementation of the MRC2014 file format.

For a full introduction and documentation, see http://mrcfile.readthedocs.io/

Functions
---------

* :func:`new`: Create a new MRC file.
* :func:`open`: Open an MRC file.
* :func:`mmap`: Open a memory-mapped MRC file (fast for large files).
* :func:`validate`: Validate an MRC file (not implemented yet!)

Basic usage
-----------

Examples assume that this package has been imported as ``mrcfile`` and numpy
has been imported as ``np``.

To open an MRC file and read a slice of data:

>>> with mrcfile.open('tests/test_data/EMD-3197.map') as mrc:
>>>     mrc.data[10,10]
array([ 2.58179283,  3.1406002 ,  3.64495397,  3.63812137,  3.61837363,
        4.0115056 ,  3.66981959,  2.07317996,  0.1251585 , -0.87975615,
        0.12517013,  2.07319379,  3.66982722,  4.0115037 ,  3.61837196,
        3.6381247 ,  3.64495087,  3.14059472,  2.58178973,  1.92690361], dtype=float32)

To create a new file with a 2D data array, and change some values:

>>> with mrcfile.new('tmp.mrc') as mrc:
>>>     mrc.set_data(np.zeros((5, 5), dtype=np.int8))
>>>     mrc.data
array([[0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0]], dtype=int8)
>>>     mrc.data[1:4,1:4] = 10
>>>     mrc.data
array([[ 0,  0,  0,  0,  0],
       [ 0, 10, 10, 10,  0],
       [ 0, 10, 10, 10,  0],
       [ 0, 10, 10, 10,  0],
       [ 0,  0,  0,  0,  0]], dtype=int8)

Background
----------

The MRC2014 format was described in the Journal of Structural Biology:
http://dx.doi.org/10.1016/j.jsb.2015.04.002

The format specification is available on the CCP-EM website:
http://www.ccpem.ac.uk/mrc_format/mrc2014.php

"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io

from .gzipmrcfile import GzipMrcFile
from .mrcfile import MrcFile
from .mrcmemmap import MrcMemmap
from .version import __version__


def new(name, data=None, gzip=False, overwrite=False):
    """Create a new MRC file.
    
    Args:
        name: The file name to use.
        data: Data to put in the file, as a numpy array. The default is None, to
            create an empty file.
        gzip: If True, the new file will be compressed with gzip. It's good
            practice to name such files with a '.gz' extension but this is not
            enforced.
        overwrite: Flag to force overwriting of an existing file. If False and a
            file of the same name already exists, the file is not overwritten
            and an exception is raised.
    
    Returns:
        An :class:`~mrcfile.mrcfile.MrcFile` object (or a
        :class:`~mrcfile.gzipmrcfile.GzipMrcFile` object if gzip=True).
    """
    NewMrc = GzipMrcFile if gzip else MrcFile
    mrc = NewMrc(name, mode='w+', overwrite=overwrite)
    if data is not None:
        mrc.set_data(data)
    return mrc


def open(name, mode='r'):  # @ReservedAssignment
    """Open an MRC file.
    
    This function opens both normal and gzip-compressed MRC files.
    
    It is possible to use this function to create new MRC files (using mode
    'w+') but the 'new' function is more flexible.
    
    Args:
        name: The file name to open.
        mode: The file mode to use. This should be one of the following: 'r' for
            read-only, 'r+' for read and write, or 'w+' for a new empty file.
            The default is 'r'.
    
    Returns:
        An :class:`~mrcfile.mrcfile.MrcFile` object (or a
        :class:`~mrcfile.gzipmrcfile.GzipMrcFile` object if the file is
        gzipped).
    
    Raises:
        ValueError: The mode is not one of 'r', 'r+' or 'w+', or the file is
            not a valid MRC file.
        IOError: The mode is 'r' or 'r+' and the file does not exist, or the
            mode is 'w+' and the file already exists. (Call :func:`new` with
            overwrite=True to deliberately overwrite an existing file.)
    
    Warnings:
        RuntimeWarning: The file appears to be a valid MRC file but the data
            block is longer than expected from the dimensions in the header.
    """
    try:
        mrc = MrcFile(name, mode=mode)
    except ValueError as orig_err:
        with io.open(name, 'rb') as f:
            magic = f.read(2)
        if magic == b'\x1f\x8b':
            mrc = GzipMrcFile(name, mode=mode)
        else:
            raise orig_err
    return mrc


def mmap(name, mode='r'):
    """Open a memory-mapped MRC file.
    
    This can allow much faster opening of large files, because the data is only
    accessed on disk when a slice is read or written from the data array. See
    the :class:`~mrcfile.mrcmemmap.MrcMemmap` class documentation for more
    information.
    
    The :class:`~mrcfile.mrcmemmap.MrcMemmap` object returned by this function
    can be used in exactly the same way as a normal
    :class:`~mrcfile.mrcfile.MrcFile` object.
    
    Args:
        name: The file name to open.
        mode: The file mode (one of 'r', 'r+' or 'w+').
    
    Returns:
        An :class:`~mrcfile.mrcmemmap.MrcMemmap` object.
    """
    return MrcMemmap(name, mode=mode)


def validate(name):
    pass
