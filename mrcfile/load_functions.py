# Copyright (c) 2018, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
load_functions
--------------

Module for top-level functions that open MRC files and form the main API of
the package.

"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io
import os

from .bzip2mrcfile import Bzip2MrcFile
from .constants import MAP_ID, MAP_ID_OFFSET_BYTES
from .gzipmrcfile import GzipMrcFile
from .mrcfile import MrcFile
from .mrcmemmap import MrcMemmap


def new(name, data=None, compression=None, overwrite=False):
    """Create a new MRC file.
    
    Args:
        name: The file name to use.
        data: Data to put in the file, as a :class:`numpy array
            <numpy.ndarray>`. The default is :data:`None`, to create an empty
            file.
        compression: The compression format to use. Acceptable values are:
            :data:`None` (the default; for no compression), ``'gzip'`` or
            ``'bzip2'``.
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
        :class:`~exceptions.ValueError`: If the compression format is not
            recognised.
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
        :class:`~exceptions.ValueError`: If the mode is not one of ``r``,
            ``r+`` or ``w+``.
        :class:`~exceptions.ValueError`: If the file is not a valid MRC file
            and ``permissive`` is :data:`False`.
        :class:`~exceptions.ValueError`: If the mode is ``w+`` and the file
            already exists. (Call :func:`new` with ``overwrite=True`` to
            deliberately overwrite an existing file.)
        :class:`~exceptions.OSError`: If the mode is ``r`` or ``r+`` and the
            file does not exist.
    
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
