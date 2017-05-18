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
...     mrc.data[10,10]
...
array([ 2.58179283,  3.1406002 ,  3.64495397,  3.63812137,  3.61837363,
        4.0115056 ,  3.66981959,  2.07317996,  0.1251585 , -0.87975615,
        0.12517013,  2.07319379,  3.66982722,  4.0115037 ,  3.61837196,
        3.6381247 ,  3.64495087,  3.14059472,  2.58178973,  1.92690361], dtype=float32)

To create a new file with a 2D data array, and change some values:

>>> with mrcfile.new('tmp.mrc') as mrc:
...     mrc.set_data(np.zeros((5, 5), dtype=np.int8))
...     mrc.data[1:4,1:4] = 10
...     mrc.data
...
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

from .bzip2mrcfile import Bzip2MrcFile
from .constants import MRC_FORMAT_VERSION, MAP_ID, MAP_ID_OFFSET_BYTES
from .gzipmrcfile import GzipMrcFile
from .mrcfile import MrcFile
from .mrcmemmap import MrcMemmap
from .version import __version__


def new(name, data=None, compression=None, overwrite=False):
    """Create a new MRC file.
    
    Args:
        name: The file name to use.
        data: Data to put in the file, as a :class:`numpy array
            <numpy.ndarray>`. The default is :data:`None`, to create an empty
            file.
        compression: The compression format to use. Acceptable values are:
            :data:`None` (the default; for no compression), ``gzip`` or
            ``bzip2``.
            It's good practice to name compressed files with an appropriate
            extension (for example, ``.mrc.gz`` for gzip) but this is not
            enforced.
        overwrite: Flag to force overwriting of an existing file. If
            :data:`False` and a file of the same name already exists, the file
            is not overwritten and an exception is raised.
    
    Returns:
        An :class:`~mrcfile.mrcfile.MrcFile` object (or a
        subclass of it if ``compression`` is specified).
    
    Raises:
        ValueError: If the compression format is not recognised.
    """
    if compression == 'gzip':
        NewMrc = GzipMrcFile
    elif compression == 'bzip2':
        NewMrc = Bzip2MrcFile
    elif compression is not None:
        raise ValueError("Unknown compression format '{0}'"
                         .format(compression))
    else:
        NewMrc = MrcFile
    mrc = NewMrc(name, mode='w+', overwrite=overwrite)
    if data is not None:
        mrc.set_data(data)
    return mrc


def open(name, mode='r', permissive=False):  # @ReservedAssignment
    """Open an MRC file.
    
    This function opens both normal and compressed MRC files. Supported
    compression formats are: gzip, bzip2.
    
    It is possible to use this function to create new MRC files (using mode
    ``w+``) but the :func:`new` function is more flexible.
    
    This function offers a permissive read mode for attempting to open corrupt
    or invalid files. In permissive mode, :mod:`warnings` are issued instead of
    exceptions if problems with the file are encountered. See
    :class:`mrcfile.mrcinterpreter.MrcInterpreter` or the
    :doc:`usage guide <../usage_guide>` for more information.
    
    Args:
        name: The file name to open.
        mode: The file mode to use. This should be one of the following: ``r``
            for read-only, ``r+`` for read and write, or ``w+`` for a new empty
            file. The default is ``r``.
        permissive: Read the file in permissive mode. The default is
            :data:`False`.
    
    Returns:
        An :class:`~mrcfile.mrcfile.MrcFile` object (or a
        :class:`~mrcfile.gzipmrcfile.GzipMrcFile` object if the file is
        gzipped).
    
    Raises:
        ValueError: If the mode is not one of ``r``, ``r+`` or ``w+``.
        ValueError: If the file is not a valid MRC file and ``permissive`` is
            :data:`False`.
        ValueError: If the mode is ``w+`` and the file already exists. (Call
            :func:`new` with ``overwrite=True`` to deliberately overwrite an
            existing file.)
        OSError: If the mode is ``r`` or ``r+`` and the file does not exist.
    
    Warns:
        RuntimeWarning: If the file appears to be a valid MRC file but the data
            block is longer than expected from the dimensions in the header.
        RuntimeWarning: If the file is not a valid MRC file and ``permissive``
            is :data:`True`.
    """
    NewMrc = MrcFile
    if os.path.exists(name):
        with io.open(name, 'rb') as f:
            start = f.read(MAP_ID_OFFSET_BYTES + len(MAP_ID))
        # Check for map ID string to avoid trying to decompress normal files
        # where the nx value happens to include the magic number for a
        # compressed format. (This still risks failing to correctly decompress
        # compressed files which happen to have 'MAP ' at position 208, but
        # that is less likely and if it does occur, the CompressedMrcFile
        # class can always be used directly instead.)
        if start[-len(MAP_ID):] != MAP_ID:
            if start[:2] == b'\x1f\x8b':
                NewMrc = GzipMrcFile
            elif start[:2] == b'BZ':
                NewMrc = Bzip2MrcFile
    return NewMrc(name, mode=mode, permissive=permissive)


def mmap(name, mode='r', permissive=False):
    """Open a memory-mapped MRC file.
    
    This allows much faster opening of large files, because the data is only
    accessed on disk when a slice is read or written from the data array. See
    the :class:`~mrcfile.mrcmemmap.MrcMemmap` class documentation for more
    information.
    
    In all other ways, :func:`mmap` behaves in exactly the same way as
    :func:`open`. The :class:`~mrcfile.mrcmemmap.MrcMemmap` object returned by
    this function can be used in exactly the same way as a normal
    :class:`~mrcfile.mrcfile.MrcFile` object.
    
    Args:
        name: The file name to open.
        mode: The file mode (one of ``r``, ``r+`` or ``w+``).
        permissive: Read the file in permissive mode. The default is
            :data:`False`.
    
    Returns:
        An :class:`~mrcfile.mrcmemmap.MrcMemmap` object.
    """
    return MrcMemmap(name, mode=mode, permissive=permissive)


def validate(name, print_file=None):
    """Validate an MRC file.
    
    This function first opens the file by calling :func:`open` (with
    ``permissive=True``), then calls :meth:`~mrcfile.mrcfile.MrcFile.validate`,
    which runs a series of tests to check whether the file complies with the
    MRC2014 format specification.
    
    If the file is completely valid, this function returns :data:`True`,
    otherwise it returns :data:`False`. Messages explaining the validation
    result will be printed to :data:`sys.stdout` by default, but if a text
    stream is given (using the ``print_file`` argument) output will be printed
    to that instead.
    
    Badly invalid files will also cause :mod:`warning <warnings>` messages to
    be issued, which will be written to :data:`sys.stderr` by default. See the
    documentation of the :mod:`warnings` module for information on how to
    suppress or capture warning output.
    
    Because the file is opened by calling :func:`open`, gzip- and
    bzip2-compressed MRC files can be validated easily using this function.
    
    After the file has been opened, it is checked for problems. The tests are:
    
    #. MRC format ID string: The ``map`` field in the header should contain
       "MAP ".
    #. Machine stamp: The machine stamp should contain one of
       ``0x44 0x44 0x00 0x00``, ``0x44 0x41 0x00 0x00`` or
       ``0x11 0x11 0x00 0x00``.
    #. MRC mode: the ``mode`` field should be one of the supported mode
       numbers: 0, 1, 2, 4 or 6.
    #. Map and cell dimensions: The header fields ``nx``, ``ny``, ``nz``,
       ``mx``, ``my``, ``mz``, ``cella.x``, ``cella.y`` and ``cella.z`` must
       all be positive numbers.
    #. Axis mapping: Header fields ``mapc``, ``mapr`` and ``maps`` must contain
       the values 1, 2, and 3 (in any order).
    #. Volume stack dimensions: If the spacegroup is in the range 401--630,
       representing a volume stack, the ``nz`` field should be exactly
       divisible by ``mz`` to represent the number of volumes in the stack.
    #. Header labels: The ``nlabl`` field should be set to indicate the number
       of labels in use, and the labels in use should appear first in the label
       array.
    #. MRC format version: The ``nversion`` field should be 20140 for
       compliance with the MRC2014 standard.
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
            Python's :func:`print` function. The default is :data:`None`, which
            means output will be printed to :data:`sys.stdout`.
    
    Returns:
        :data:`True` if the file is valid, or :data:`False` if the file does
        not meet the MRC format specification in any way.
    
    Raises:
        OSError: If the file does not exist or cannot be opened.
    
    Warns:
        RuntimeWarning: If the file is seriously invalid because it has no map
            ID string, an incorrect machine stamp, an unknown mode number, or
            is not the same size as expected from the header.
    """
    with open(name, permissive=True) as mrc:
        return mrc.validate(print_file=print_file)
