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
import os

from .constants import MRC_FORMAT_VERSION, MAP_ID, MAP_ID_OFFSET_BYTES
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


def open(name, mode='r', permissive=False):  # @ReservedAssignment
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
        ValueError: If the mode is not one of 'r', 'r+' or 'w+', or the file
            is not a valid MRC file, , or the mode is 'w+' and the file
            already exists. (Call :func:`new` with overwrite=True to
            deliberately overwrite an existing file.)
        OSError: If the mode is 'r' or 'r+' and the file does not exist.
    
    Warns:
        RuntimeWarning: If the file appears to be a valid MRC file but the data
            block is longer than expected from the dimensions in the header.
    """
    NewMrc = MrcFile
    if os.path.exists(name):
        with io.open(name, 'rb') as f:
            start = f.read(MAP_ID_OFFSET_BYTES + len(MAP_ID))
        if start[:2] == b'\x1f\x8b' and start[-len(MAP_ID):] != MAP_ID:
            NewMrc = GzipMrcFile
    return NewMrc(name, mode=mode, permissive=permissive)


def mmap(name, mode='r', permissive=False):
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
    return MrcMemmap(name, mode=mode, permissive=permissive)


def validate(name, print_file=None):
    """Validate an MRC file.
    
    This function first opens the file by calling :func:`open`, then calls
    :meth:`~mrcfile.mrcfile.MrcFile.validate`, which runs a series of tests to
    check whether the file complies with the MRC2014 format specification. If
    the file is completely valid, this function returns ``True``, otherwise it
    returns ``False``. Messages explaining the validation result will be printed
    to ``sys.stdout`` by default, but if a text stream is given (using the
    ``print_file`` argument) output will be printed to that instead.
    
    Because the file is opened by calling :func:`open`, gzipped MRC files can
    also be validated.
    
    After the file has been successfully opened, it is tested for more minor
    problems. The tests are:
    
    #. MRC format ID string: The ``map`` field in the header should contain
       "MAP ".
    #. Machine stamp: The machine stamp should contain one of
       ``0x44 0x44 0x00 0x00``, ``0x44 0x41 0x00 0x00`` or
       ``0x11 0x11 0x00 0x00``.
    #. MRC mode: the ``mode`` field should be one of the supported mode
       numbers: 0, 1, 2, 4 or 6.
    #. Map and cell dimensions: The header fields ``nx``, ``ny``, ``nz``,
       ``mx``, ``my``, ``mz``, ``cella.x``, ``cella.y`` and ``cella.z`` must all
       be positive numbers.
    #. Axis mapping: Header fields ``mapc``, ``mapr`` and ``maps`` must contain
       the values 1, 2, and 3 (in any order).
    #. Volume stack dimensions: If the spacegroup is in the range 401--630,
       representing a volume stack, the ``nz`` field should be exactly divisible
       by ``mz`` to represent the number of volumes in the stack.
    #. Header labels: The ``nlabl`` field should be set to indicate the number
       of labels in use, and the labels in use should appear first in the label
       array.
    #. MRC format version: The ``nversion`` field should be 20140 for compliance
       with the MRC2014 standard.
    #. Extended header type: If an extended header is present, the ``exttyp``
       field should be set to indicate the type of extended header.
    #. Data statistics: The statistics in the header should be correct for the
       actual data in the file, or marked as undetermined.
    #. File size: The size of the file on disk should match the expected size
       calculated from the MRC header.
    
    Args:
        name: The file name to open and validate.
        print_file: The output text stream to use for printing messages about
            the validation. This is passed directly to the ``file`` argument of
            Python's ``print()`` function. The default is ``None``, which means
            output will be printed to ``sys.stdout``.
    
    Returns:
        ``True`` if the file is valid, ``False`` if the file does not meet the
        MRC format specification in any way.
    
    Raises:
        OSError: If the file does not exist or cannot be opened.
        ValueError: If the file is seriously invalid, because it has no format
            ID string, an incorrect machine stamp or is smaller than expected
            from the header.
    
    Warns:
        RuntimeWarning: If the file appears to be a valid MRC file but the data
            block is longer than expected from the dimensions in the header.
            This information will also be printed to the output stream.
    """
    with open(name, permissive=True) as mrc:
        return mrc.validate(print_file=print_file)
