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

import numpy as np

from .constants import MRC_FORMAT_VERSION
from .gzipmrcfile import GzipMrcFile
from .mrcfile import MrcFile
from .mrcmemmap import MrcMemmap
from .utils import spacegroup_is_volume_stack
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
        ValueError: If the mode is not one of 'r', 'r+' or 'w+', the file is
            not a valid MRC file, , or the mode is 'w+' and the file already
            exists. (Call :func:`new` with overwrite=True to deliberately
            overwrite an existing file.)
        OSError: If the mode is 'r' or 'r+' and the file does not exist.
    
    Warns:
        RuntimeWarning: If the file appears to be a valid MRC file but the data
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


def validate(name, print_file=None):
    """Validate an MRC file.
    
    This function first opens the file by calling :func:`open`, then runs a
    series of tests to check whether the file complies with the MRC2014 format
    specification. Using the :func:`open` function like this has two
    implications:
    
    * gzipped MRC files can also be validated.
    * files which are badly invalid will raise a ValueError before reaching the
      rest of the validation tests. This will happen if the file does not have
      the correct format ID string, has an invalid machine stamp, is smaller
      than expected, or the mode number is not recognised.
    
    After the file has been successfully opened, it is tested for more minor
    problems. The tests are:
    
    #. File size: The size of the file on disk should match the expected size
       calculated from the MRC header.
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
    
    Args:
        name: The file name to open and validate.
        print_file: The output text stream to use for printing messages about
            the validation. This is passed directly to the ``file`` argument of
            Python's ``print()`` function. The default is ``None``, which means
            output will be printed to ``sys.stdout``.
    
    Returns:
        True if the file is valid, False if the file does not meet the MRC
        format specification in any way.
    
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
    valid = True
    
    def log(message):
        print(message, file=print_file)
    
    with open(name) as mrc:
        # Check file size
        mrc._iostream.seek(0)
        mrc._iostream.read()
        file_size = mrc._iostream.tell()
        mrc_size = mrc.header.nbytes + mrc.extended_header.nbytes + mrc.data.nbytes
        if (file_size != mrc_size):
            log("File is larger than expected. Actual size: {0} bytes; "
                "expected size: {1} bytes (calculated from header)"
                .format(file_size, mrc_size))
            valid = False
        
        # Check map dimensions and other fields are non-negative
        for field in ['nx', 'ny', 'nz', 'mx', 'my', 'mz', 'ispg', 'nlabl']:
            if mrc.header[field] < 0:
                log("Header field '{0}' is negative".format(field))
                valid = False
        
        # Check cell dimensions are non-negative
        for field in ['x', 'y', 'z']:
            if mrc.header.cella[field] < 0:
                log("Cell dimension '{0}' is negative".format(field))
                valid = False
        
        # Check axis mapping is valid
        axes = set()
        for field in ['mapc', 'mapr', 'maps']:
            axes.add(int(mrc.header[field]))
        if axes != set([1, 2, 3]):
            log("Invalid axis mapping: found {0}, should be [1, 2, 3]"
                .format(sorted(list(axes))))
            valid = False
        
        # Check mz value for volume stacks
        if spacegroup_is_volume_stack(mrc.header.ispg):
            if mrc.header.nz % mrc.header.mz != 0:
                log("Error in dimensions for volume stack: nz should be "
                    "divisible by mz. Found nz = {0}, mz = {1})"
                    .format(mrc.header.nz, mrc.header.mz))
                valid = False
        
        # Check nlabl is correct
        count = 0
        seen_empty_label = False
        for label in mrc.header.label:
            if len(label.strip()) > 0:
                count += 1
                if seen_empty_label:
                    log("Error in header labels: empty labels appear between "
                        "text-containing labels")
                    valid = False
            else:
                seen_empty_label = True
        if count != mrc.header.nlabl:
            log("Error in header labels: nlabl is {0} "
                "but {1} labels contain text".format(mrc.header.nlabl, count))
            valid = False
        
        # Check MRC format version
        if mrc.header.nversion != MRC_FORMAT_VERSION:
            log("File does not declare MRC format version 20140: nversion = {0}"
                .format(mrc.header.nversion))
            valid = False
        
        # Check extended header type is set to a known value
        valid_exttypes = ['CCP4', 'MRCO', 'SERI', 'AGAR', 'FEI1']
        if mrc.header.nsymbt > 0 and mrc.header.exttyp not in valid_exttypes:
            log("Extended header type is undefined or unrecognised: exttyp = "
                "'{0}'".format(mrc.header.exttyp.item().decode('ascii')))
            valid = False
        
        # Check data statistics
        real_rms = real_min = real_max = real_mean = 0
        if len(mrc.data > 0):
            real_rms = mrc.data.std()
            real_min = mrc.data.min()
            real_max = mrc.data.max()
            real_mean = mrc.data.mean()
        if (mrc.header.rms >= 0 and not np.isclose(real_rms, mrc.header.rms)):
            log("Error in data statistics: RMS deviation is {0} but the value "
                "in the header is {1}".format(real_rms, mrc.header.rms))
            valid = False
        if mrc.header.dmin < mrc.header.dmax and mrc.header.dmin != real_min:
            log("Error in data statistics: minimum is {0} but the value "
                "in the header is {1}".format(real_min, mrc.header.dmin))
            valid = False
        if mrc.header.dmin < mrc.header.dmax and mrc.header.dmax != real_max:
            log("Error in data statistics: maximum is {0} but the value "
                "in the header is {1}".format(real_max, mrc.header.dmax))
            valid = False
        if (mrc.header.dmean > min(mrc.header.dmin, mrc.header.dmax)
            and not np.isclose(real_mean, mrc.header.dmean)):
            log("Error in data statistics: mean is {0} but the value "
                "in the header is {1}".format(real_mean, mrc.header.dmean))
            valid = False
    
    return valid
