# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
TODO:
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime
import os
import sys

import numpy as np

from .dtypes import HEADER_DTYPE

# Constants
MRC_FORMAT_VERSION = 20140 # MRC2014 format, version 0

IMAGE_STACK_SPACEGROUP = 0
VOLUME_SPACEGROUP = 1
VOLUME_STACK_SPACEGROUP = 401

MAP_ID = b'MAP '
MAP_ID_OFFSET_BYTES = 208  # location of 'MAP ' string in an MRC file


def create_default_header():
    """Create a default MRC file header.
    
    The header is initialised with standard file type and version information,
    default values for some essential fields, and zeros elsewhere. The first
    text label is also set to indicate the file was created by this module.
    
    Returns:
        The new header, as a structured numpy record array.
    """
    header = np.zeros(shape=(), dtype=HEADER_DTYPE).view(np.recarray)
    header.map = MAP_ID
    header.nversion = MRC_FORMAT_VERSION
    header.machst = machine_stamp_from_byte_order(header.mode.dtype.byteorder)
    
    # Default space group is P1
    header.ispg = VOLUME_SPACEGROUP
    
    # Standard cell angles all 90.0 degrees
    default_cell_angle = 90.0
    header.cellb.alpha = default_cell_angle
    header.cellb.beta = default_cell_angle
    header.cellb.gamma = default_cell_angle
    # (this can also be achieved by assigning a 3-tuple to header.cellb directly
    # but using the sub-fields individually is easier to read and understand)
    
    # Standard axes: columns = X, rows = Y, sections = Z
    header.mapc = 1
    header.mapr = 2
    header.maps = 3
    
    reset_header_stats(header)
    
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header.label[0] = '{0:40s}{1:>40s}'.format('Created by mrcfile.py', time)
    header.nlabl = 1
    
    return header


def reset_header_stats(header):
    """Set the header statistics to indicate that the values are undetermined.
    
    Args:
        header: The header to modify.
    """
    header.dmin = 0
    header.dmax = -1
    header.dmean = -2
    header.rms = -1


def read_header(data_file):
    """Read the MRC header from the given file object.
    
    The header will be read from the current file pointer position, and the file
    pointer will be advanced by 1024 bytes.
    
    Args:
        file: A Python file-like object, which should be open in binary mode.
    
    Returns:
        The file header, as a structured numpy record array.
    
    Raises:
        ValueError: The file is not a valid MRC file.
    """
    # Read 1024 bytes from the stream
    header_str = data_file.read(HEADER_DTYPE.itemsize)
    
    # Use a recarray to allow access to fields as attributes
    # (e.g. header.mode instead of header['mode'])
    header = np.rec.fromstring(header_str, dtype=HEADER_DTYPE, shape=())
    
    # Make header writeable, because fromstring() creates a read-only array
    header.flags.writeable = True
    
    # Check this is an MRC file, and read machine stamp to get byte order
    if header.map != MAP_ID:
        raise ValueError('Map ID string not found - not an MRC file, '
                         'or file is corrupt')
    
    machst = header.machst
    if machst[0] == 0x44 and machst[1] in (0x44, 0x41):
        byte_order = '<'
    elif (machst[0] == 0x11 and machst[1] == 0x11):
        byte_order = '>'
    else:
        raise ValueError('Unrecognised machine stamp: '
                         + ' '.join('0x{:02x}'.format(byte) for byte in machst))
    
    # Create a new dtype with the correct byte order and update the header
    header.dtype = header.dtype.newbyteorder(byte_order)
    
    return header


def update_header_from_data(header, data):
    """Update the given MRC file header from the given data array.
    
    TODO: explain space group changes
    
    This function updates the header byte order and machine stamp to match the
    byte order of the data. It also updates the file mode, space group and the
    dimension fields nx, ny, nz, mx, my and mz.
    
    Note that this function does *not* update the data statistics fields in the
    header (min, max, mean and rms). Use the update_header_stats() function to
    update the statistics. (This is for performance reasons -- updating the
    statistics can take a long time for large data sets, but updating the other
    header information is always fast because only the type and shape of the
    data array need to be inspected.)
    
    Args:
        header: The header to update, as a numpy record array. The header will
            be updated in-place.
        data: A numpy array containing the data.
    """
    # Check the dtype is one we can handle and update mode to match
    header.mode = mode_from_dtype(data.dtype)
    
    # Ensure header byte order and machine stamp match the data's byte order
    byte_order = data.dtype.byteorder
    if byte_order != '|' and header.mode.dtype.byteorder != byte_order:
        header.byteswap(True)
        header.dtype = header.dtype.newbyteorder(byte_order)
    header.machst = machine_stamp_from_byte_order(header.mode.dtype.byteorder)
    
    shape = data.shape
    axes = len(shape)
    if axes == 2:
        # Single image. Space group 0, nz = mz = 1
        header.ispg = IMAGE_STACK_SPACEGROUP
        header.nx = header.mx = shape[1]
        header.ny = header.my = shape[0]
        header.nz = header.mz = 1
    elif axes == 3:
        header.nx = header.mx = shape[2]
        header.ny = header.my = shape[1]
        if header.ispg == IMAGE_STACK_SPACEGROUP:
            # Image stack. mz = 1, nz = sections in the volume
            header.mz = 1
            header.nz = shape[0]
        else:
            # Volume. nz = mz = sections in the volume
            header.nz = header.mz = shape[0]
    elif axes == 4:
        # Volume stack. Space group 401, mz = secs per vol, nz = total sections
        if not spacegroup_is_volume_stack(header.ispg):
            header.ispg = VOLUME_STACK_SPACEGROUP
        header.nx = header.mx = shape[3]
        header.ny = header.my = shape[2]
        header.mz = shape[1]
        header.nz = shape[0] * shape[1]
    else:
        raise ValueError('Data must be 2-, 3- or 4-dimensional')


def update_header_stats(header, data):
    """Update the header's dmin, dmax, dmean and rms fields from the data.
    
    Note that this can take some time with large files, particularly with files
    larger than the currently available memory. The rms/standard deviation
    calculation is the most time-consuming so this can be switched off using
    the include_rms parameter.
    
    Args:
        header: The header to update, as a numpy record array.
        data: A numpy array containing the data to summarise.
    """
    header.dmin = data.min()
    header.dmax = data.max()
    
    # Use a float64 accumulator to calculate mean and standard deviation
    # This prevents overflow errors during calculation
    header.dmean = np.float32(data.mean(dtype=np.float64))
    header.rms = np.float32(data.std(dtype=np.float64))


def print_header(header):
    """Print the contents of all header fields.
    
    Args:
        header: The header to print, as a structured numpy array.
    """
    for item in header.dtype.names:
        print('{0:15s} : {1}'.format(item, header[item]))


_dtype_to_mode = dict(f2=2, f4=2, i1=0, i2=1, u1=6, u2=6, c8=4)

def mode_from_dtype(dtype):
    """Return the MRC mode number corresponding to the given numpy dtype.
    
    The conversion is as follows:
    
    float16   -> mode 2 (data will be widened to 32 bits in the file)
    float32   -> mode 2
    int8      -> mode 0
    int16     -> mode 1
    uint8     -> mode 6 (data will be widened to 16 bits in the file)
    uint16    -> mode 6
    complex64 -> mode 4
    
    Note that there is no numpy dtype which corresponds to MRC mode 3.
    
    Args:
        dtype: A numpy dtype object.
    
    Returns:
        The MRC mode number.
    
    Raises:
        ValueError: There is no corresponding MRC mode for the given dtype.
    """
    kind_and_size = dtype.kind + str(dtype.itemsize)
    if kind_and_size in _dtype_to_mode:
        return _dtype_to_mode[kind_and_size]
    raise ValueError("dtype '{0}' cannot be converted "
                     "to an MRC file mode".format(dtype))

_mode_to_dtype = { 0: np.int8,
                   1: np.int16,
                   2: np.float32,
                   4: np.complex64,
                   6: np.uint16 }

def dtype_from_mode(mode):
    """Return the numpy dtype corresponding to the given MRC mode number.
    
    The mode parameter may be given as a Python scalar, numpy scalar or
    single-item numpy array.
    
    The conversion is as follows:
    
    mode 0 -> int8
    mode 1 -> int16
    mode 2 -> float32
    mode 4 -> complex64
    mode 6 -> uint16
    
    Note that mode 3 is not supported as there is no matching numpy dtype.
    
    Args:
        mode: The MRC mode number. This may be given as any type which can be
            converted to an int, for example a Python scalar (int or float),
            a numpy scalar or a single-item numpy array.
    
    Returns:
        The numpy dtype object corresponding to the given mode.
    
    Raises:
        ValueError: There is no corresponding dtype for the given mode.
    """
    # TODO: read mode 3 in some way - as int32 or structured types, maybe?
    # Also maybe IMOD's mode 16 and mode 0 uint8 variant?
    mode = int(mode)
    if mode in _mode_to_dtype:
        return np.dtype(_mode_to_dtype[mode])
    else:
        raise ValueError("Unrecognised mode '{0}'".format(mode))


_byte_order_to_machine_stamp = {'<': bytearray((0x44, 0x44, 0, 0)),
                                '>': bytearray((0x11, 0x11, 0, 0))}

def machine_stamp_from_byte_order(byte_order='='):
    """Return the machine stamp corresponding to the given byte order indicator.
    
    Args:
        byte_order: The byte order indicator: one of '=', '<' or '>', as
            defined and used by numpy dtype objects.
    
    Returns:
        The machine stamp which corresponds to the given byte order, as a
        bytearray. This will be either (0x44, 0x44, 0, 0) for little-endian
        or (0x11, 0x11, 0, 0) for big-endian. If the given byte order indicator
        is '=', the native byte order is used.
    
    Raises:
        ValueError: The byte order indicator is unrecognised.
    """
    # If byte order is '=', replace it with the system-native order
    if byte_order == '=':
        byte_order = '<' if sys.byteorder == 'little' else '>'
    
    if byte_order in _byte_order_to_machine_stamp:
        return _byte_order_to_machine_stamp[byte_order]
    else:
        raise ValueError("Unrecognised byte order "
                         "indicator '{0}'".format(byte_order))

def spacegroup_is_volume_stack(ispg):
    return 401 <= ispg <= 630
