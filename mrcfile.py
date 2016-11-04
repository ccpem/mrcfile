# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
TODO: module docstring
"""

# TODO: main improvements to make:
# - handle axis swapping (?)
# - ability to create a large empty file to be filled piecemeal
# - handle different mx & nx values etc
# IMOD - header correctly calculates pixel size as cella.x / mx, but 3dmod
# gives distances assuming X spacing applies in all dimensions, and applies it
# on a map of nx * ny * nz pixels (where it is probably wrong since it's calculated
# from mx, not nx).

# Format specifications:
# http://www.ccpem.ac.uk/mrc_format/mrc2014.php (official)
# http://www.ccp4.ac.uk/html/maplib.html (CCP4 version)
# http://bio3d.colorado.edu/imod/doc/mrc_format.txt (IMOD version)
# http://www.2dx.unibas.ch/documentation/mrc-software/fei-extended-mrc-format-not-used-by-2dx

# Paper describing MRC2014 format: http://dx.doi.org/10.1016/j.jsb.2015.04.002

# Import Python 3 features for future-proofing
# Deliberately do NOT import unicode_literals due to a bug in numpy dtypes:
# https://github.com/numpy/numpy/issues/2407
from __future__ import absolute_import, division, print_function

__version__ = '0.0.0'

from datetime import datetime
import os
import numpy as np
import sys

MRC_FORMAT_VERSION = 20140  # MRC2014 format, version 0

IMAGE_STACK_SPACEGROUP = 0
VOLUME_SPACEGROUP = 1
VOLUME_STACK_SPACEGROUP = 401

HEADER_DTYPE = np.dtype([
    ('nx', 'i4'),         # Number of columns
    ('ny', 'i4'),         # Number of rows
    ('nz', 'i4'),         # Number of sections

    ('mode', 'i4'),       # Mode; indicates type of values stored in data block

    ('nxstart', 'i4'),    # Starting point of sub-image
    ('nystart', 'i4'),
    ('nzstart', 'i4'),

    ('mx', 'i4'),         # Grid size in X, Y and Z
    ('my', 'i4'),
    ('mz', 'i4'),

    ('cella', [           # Cell size in angstroms
        ('x', 'f4'),
        ('y', 'f4'),
        ('z', 'f4')
    ]),

    ('cellb', [           # Cell angles in degrees
        ('alpha', 'f4'),
        ('beta', 'f4'),
        ('gamma', 'f4')
    ]),

    ('mapc', 'i4'),        # map column  1=x,2=y,3=z.
    ('mapr', 'i4'),        # map row     1=x,2=y,3=z.
    ('maps', 'i4'),        # map section 1=x,2=y,3=z.

    ('dmin', 'f4'),        # Minimum pixel value
    ('dmax', 'f4'),        # Maximum pixel value
    ('dmean', 'f4'),       # Mean pixel value

    ('ispg', 'i4'),        # space group number
    ('nsymbt', 'i4'),      # number of bytes in extended header

    ('extra1', 'V8'),      # extra space, usage varies by application
    ('exttyp', 'S4'),      # code for the type of extended header
    ('nversion', 'i4'),    # version of the MRC format
    ('extra2', 'V84'),     # extra space, usage varies by application

    ('origin', [           # Origin of image
        ('x', 'f4'),
        ('y', 'f4'),
        ('z', 'f4')
    ]),

    ('map', 'S4'),         # Contains 'MAP ' to identify file type
    ('machst', 'u1', 4),   # Machine stamp; identifies byte order

    ('rms', 'f4'),         # RMS deviation of densities from mean density

    ('nlabl', 'i4'),       # Number of labels with useful data
    ('label', 'S80', 10)   # 10 labels of 80 characters
])

MAP_ID = b'MAP '
MAP_ID_OFFSET_BYTES = 208  # location of 'MAP ' string in an MRC file

class MrcFile(object):
    """An object representing an MRC / CCP4 map file.

    The header and data of the file are presented as numpy arrays.

    Note that the data array is mapped directly from the underlying file. If you
    keep a reference to it and change the data values, the file will still be
    changed even if this MrcFile object has been closed. To try to prevent this,
    the 'writeable' flag is set to False on the old data array whenever it is
    closed or replaced with a new array.

    Usage: TODO:
    """

    def __init__(self, name, mode='r', overwrite=False):
        """
        Initialiser. This is where we read the file header and data.

        Header values are stored in a structured numpy array. To get numeric
        values from them it might be necessary to use the item() method:
        >>> header['mode']
        TODO: finish

        """
        super(MrcFile, self).__init__()

        if mode not in ['r', 'r+', 'w+']:
            raise ValueError("Mode '{0}' not supported".format(mode))

        if ('w' in mode and os.path.exists(name) and not overwrite):
            raise IOError("File '{0}' already exists; set overwrite=True"
                          "to overwrite it".format(name))

        self._is_image_stack = False   # Treat 3D data as a volume by default
        self._read_only = (mode == 'r')
        self._file = open(name, mode + 'b')

        try:
            if 'w' in mode:
                # New file. Create a default header and truncate the file to the
                # standard header size (1024 bytes).
                self.header = create_default_header()
                self._file.truncate(self.header.nbytes)
            else:
                # Existing file. Read the header.
                self._read_header()

            # Now we have a header (default or from the file) we can read the
            # extended header and data arrays, which will be empty if this is a
            # new file
            self._read_extended_header()
            self._read_data()
        except Exception:
            self._file.close()
            raise


    @property
    def extended_header(self):
        """Get or set the file's extended header as a numpy array.

        By default the dtype of the extended header array is void (raw data,
        dtype 'V'). If the actual data type of the extended header is known, the
        dtype of the array can be changed to match.

        Note that the file's entire data block must be moved if the extended
        header size changes. Setting a new extended header can therefore be
        very time consuming with large files.
        """
        return self.__extended_header


    @extended_header.setter
    def extended_header(self, extended_header):
        if self._read_only:
            raise ValueError('This file is read-only')
        if extended_header.nbytes != self.__extended_header.nbytes:
            data_copy = self.__data.copy()
            self._close_memmap()
            self.__extended_header = extended_header
            self.header.nsymbt = extended_header.nbytes
            header_nbytes = self.header.nbytes + extended_header.nbytes
            self._file.truncate(header_nbytes + data_copy.nbytes)
            self._open_memmap(data_copy.dtype, data_copy.shape)
            np.copyto(self.__data, data_copy)
        else:
            self.__extended_header = extended_header


    @property
    def data(self):
        """Get or set the file's current data block as a numpy array.

        Setting the data field will replace the current data with a copy of the
        given array, and update the header to match the new data dimensions. The
        data statistics (min, max, mean, rms) stored in the header will also be
        updated.

        If the data array is modified in-place, the header statistics will not
        be updated automatically. Call update_header_stats() to update them if
        required -- this is usually a good idea, but can take a long time for
        large files.
        """
        return self.__data


    @data.setter
    def data(self, data):
        if self._read_only:
            raise ValueError('This file is read-only')

        # Copy the header and update it from the data
        # We use a copy so the current header and data will remain unchanged
        # if the new data is invalid and an exception is raised
        new_header = self.header.copy()
        update_header_from_data(new_header, data)
        if data.size > 0:
            update_header_stats(new_header, data)
        else:
            reset_header_stats(new_header)

        # The dtype of the new memmap array might not be the same as the given
        # data array. For example if an array of unsigned bytes is given, they
        # should be written in mode 6 as unsigned 16-bit ints to avoid data
        # loss. So, we construct a new dtype to use for the file's data array.
        mode = new_header.mode
        dtype = dtype_from_mode(mode).newbyteorder(mode.dtype.byteorder)

        # Ensure we can use 'safe' casting to copy the data into the file.
        # This should guarantee we are not accidentally performing a narrowing
        # type conversion and potentially losing data. If this assertion fails
        # there is probably an error in the logic which converts MRC modes to
        # and from dtypes.
        assert np.can_cast(data, dtype, casting='safe')

        # At this point, we know the data is valid, so we go ahead with the swap
        # First, close the old memmap and replace the header with the new one
        self._close_memmap()
        self.header = new_header

        # Next, truncate the file to the new size (this should be safe to do
        # whether the new size is smaller, greater or the same as the old size)
        header_nbytes = self.header.nbytes + self.extended_header.nbytes
        self._file.truncate(header_nbytes + data.nbytes)

        # Now, open a new memmap of the correct shape, size and dtype
        self._open_memmap(dtype, data.shape)

        # Finally, copy the new data into the memmap
        np.copyto(self.__data, data, casting='safe')


    @property
    def voxel_size(self):
        """Get or set the voxel size in angstroms.
        
        The voxel size is returned as a structured numpy record array with three
        fields (x, y and z). Because the array is produced by calculation from
        values in the header, changes to it will *not* cause any changes in the
        file.
        
        To set the voxel size, assign a value to the voxel_size attribute. You
        may give a single number, a 3-tuple (x, y ,z) or a modified version of
        the voxel_size array. The following examples are all equivalent:
        
        >>> mrc.voxel_size = 1.0
        
        >>> mrc.voxel_size = (1.0, 1.0, 1.0)
        
        >>> vox_sizes = mrc.voxel_size
        >>> vox_sizes.x = 1.0
        >>> vox_sizes.y = 1.0
        >>> vox_sizes.z = 1.0
        >>> mrc.voxel_size = vox_sizes
        """
        x = self.header.cella.x / self.header.mx
        y = self.header.cella.y / self.header.my
        z = self.header.cella.z / self.header.mz
        sizes = np.rec.array((x, y, z),
                             dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
        sizes.flags.writeable = False
        return sizes


    @voxel_size.setter
    def voxel_size(self, voxel_size):
        try:
            # First, assume we have a single numeric value
            sizes = (float(voxel_size),) * 3
        except TypeError:
            try:
                # Not a single value. Next, if voxel_size is an array (as
                # produced by the voxel_size getter), item() gives a 3-tuple
                sizes = voxel_size.item()
            except AttributeError:
                # If the item() method doesn't exist, assume we have a 3-tuple
                sizes = voxel_size
        self._set_voxel_size(*sizes)


    def _set_voxel_size(self, x_size, y_size, z_size):
        """Set the voxel size for the file.
        
        Args:
            x_size: The voxel size in the X direction, in angstroms
            y_size: The voxel size in the Y direction, in angstroms
            z_size: The voxel size in the Z direction, in angstroms
        """
        self.header.cella.x = x_size * self.header.mx
        self.header.cella.y = y_size * self.header.my
        self.header.cella.z = z_size * self.header.mz


    def is_single_image(self):
        return self.data.ndim == 2


    def is_image_stack(self):
        return self.data.ndim == 3 and self._is_image_stack


    def is_volume(self):
        return self.data.ndim == 3 and not self._is_image_stack


    def is_volume_stack(self):
        return self.data.ndim == 4


    def set_image_stack(self):
        if self.data.ndim != 3:
            raise ValueError('Only 3D data can be changed into an image stack')
        self._is_image_stack = True
        self._update_header_from_data()


    def set_volume(self):
        if self.data.ndim != 3:
            raise ValueError('Only 3D data can be changed into a volume')
        self._is_image_stack = False
        self._update_header_from_data()


    def close(self):
        """Flush any changes to disk and close the file."""
        if not self._file.closed:
            self.flush()
            self._close_memmap()
            self._file.close()
        self.header = None


    def flush(self):
        """Flush the header and data arrays to the file buffer."""
        if not self._read_only:
            self._update_header_from_data()
            self._write_header()

            # Flushing the file before the mmap makes the mmap flush faster
            self._file.flush()
            self.__data.flush()
            self._file.flush()


    def __repr__(self):
        return "MrcFile('{0}', mode='{1}')".format(self._file.name,
                                                   self._file.mode[:-1])


    def __enter__(self):
        """Called by the context manager at the start of a 'with' block.

        Returns:
            This object (self) since it represents the open file.
        """
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called by the context manager at the end of a 'with' block.

        This ensures that the close() method is called.
        """
        self.close()


    def __del__(self):
        """Attempt to close the file when this object is garbage collected.

        It's better not to rely on this - instead, use a 'with' block or
        explicitly call the close() method.
        """
        try:
            self.close()
        except AttributeError:
            # Probably the file was never opened and self._file doesn't exist
            pass


    def _read_header(self):
        """Read the header from the file."""
        self.header = read_header(self._file)
        self.header.flags.writeable = not self._read_only


    def _read_extended_header(self):
        """Read the extended header from the file.
        
        If there is no extended header, a zero-length array is assigned to the
        extended_header field.
        """
        ext_header_size = self.header.nsymbt
        if ext_header_size > 0:
            self._file.seek(self.header.nbytes, os.SEEK_SET)
            ext_header_bytes = self._file.read(ext_header_size)
            self.__extended_header = np.array(ext_header_bytes, dtype='V')
        else:
            self.__extended_header = np.array((), dtype='V')

        self.extended_header.flags.writeable = not self._read_only


    def _read_data(self):
        """Read the data block from the file.
        
        This method first calculates the parameters needed to read the data
        (block start position, endian-ness, file mode) and then opens the data
        as a numpy memmap array.
        """

        mode = self.header.mode
        dtype = dtype_from_mode(mode).newbyteorder(mode.dtype.byteorder)

        # data dimensions
        nx = self.header.nx
        ny = self.header.ny
        nz = self.header.nz
        mx = self.header.mx
        my = self.header.my
        mz = self.header.mz
        ispg = self.header.ispg

        # TODO: need to decide how to handle case where nx != mx - which to use for shape, pixel size calc etc?
        assert nx == mx
        assert ny == my

        # Convert to array shape
        if ispg == VOLUME_STACK_SPACEGROUP:
            assert nz >= mz
            assert nz % mz == 0
            shape = (nz // mz, mz, ny, nx)
        elif ispg == VOLUME_SPACEGROUP:
            shape = (nz, ny, nx)
        elif ispg == IMAGE_STACK_SPACEGROUP:
            assert nz >= 0
            if nz > 1:
                shape = (nz, ny, nx)
                self._is_image_stack = True
            else:
                # Use a 2D array for a single image
                shape = (ny, nx)
        else:
            raise ValueError("Unrecognised space group '{0}'".format(ispg))

        header_size = self.header.nbytes + self.header.nsymbt
        data_size = nx * ny * nz * dtype.itemsize


        #####################################
        # memmap version:
        #
        self._file.seek(0, os.SEEK_END)
        file_size = self._file.tell()
        assert file_size == header_size + data_size

        self._open_memmap(dtype, shape)


        ######################################
        # normal array version:
        #
#         self._seek_to_data_block()
#         data_str = self._file.read(data_size)
#
#         # Make sure that we have read the whole file
#         assert not self._file.read()
#
#         # Read data
#         self.data = np.ndarray(shape=shape, dtype=dtype, buffer=data_str)


    def _update_header_from_data(self):
        if self._read_only:
            raise ValueError('This file is read-only')
        update_header_from_data(self.header, self.data, self._is_image_stack)


    def _write_header(self):
        self._file.seek(0)
        self._file.write(self.header)
        self._file.write(self.extended_header)


    def _open_memmap(self, dtype, shape):
        """Open a new memmap array pointing at the file's data block."""
        acc_mode = 'r' if self._read_only else 'r+'
        header_nbytes = self.header.nbytes + self.header.nsymbt

        self._file.flush()
        self.__data = np.memmap(self._file,
                                dtype=dtype,
                                mode=acc_mode,
                                offset=header_nbytes,
                                shape=shape)


    def _close_memmap(self):
        """Delete the existing memmap array, if it exists.
        
        The array is flagged as read-only before deletion, so if a reference to
        it has been kept elsewhere, changes to it should no longer be able to
        change the file contents.
        """
        try:
            self.__data.flush()
            self.__data.flags.writeable = False
            del self.__data
        except AttributeError:
            pass


    def print_header(self):
        """Print the file header."""
        print_header(self.header)


    def update_header_stats(self):
        """Update the header statistics with accurate values from the data."""
        update_header_stats(self.header, self.data)



def create_default_header():
    """Create a default MRC file header.

    The header is initialised with standard file type and version information,
    90.0 degree cell angles, default axes, and statistics fields set to
    indicate undetermined values. The first text label is set to indicate the
    file was created by this Python module along with a timestamp. Other header
    fields are set to zero.

    Returns:
        The new header, as a structured numpy record array.
    """
    header = np.zeros(shape=(), dtype=HEADER_DTYPE).view(np.recarray)
    header.map = MAP_ID
    header.nversion = MRC_FORMAT_VERSION
    header.machst = machine_stamp_from_byte_order(header.mode.dtype.byteorder)

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

    The header will be read from the beginning of the file, regardless of the
    current file pointer position.

    Args:
        file: A Python file-like object, which should be open in binary mode.

    Returns:
        The file header, as a structured numpy record array.

    Raises:
        ValueError: The file is not a valid MRC file.
    """
    # Check this is an MRC file, and read machine stamp to get byte order
    data_file.seek(MAP_ID_OFFSET_BYTES, os.SEEK_SET)
    map_str = data_file.read(4)
    if map_str != MAP_ID:
        raise ValueError('Map ID string not found - not an MRC file, '
                         'or file is corrupt')

    machst = bytearray(data_file.read(4))
    if machst[0] == 0x44 and machst[1] in (0x44, 0x41):
        byte_order = '<'
    elif (machst[0] == 0x11 and machst[1] == 0x11):
        byte_order = '>'
    else:
        raise ValueError('Unrecognised machine stamp: '
                         + ' '.join('0x{:02x}'.format(byte) for byte in machst))

    # Prepare to read header
    header_dtype = HEADER_DTYPE.newbyteorder(byte_order)
    data_file.seek(0)

    # Use a recarray to allow access to fields as attributes
    # (e.g. header.mode instead of header['mode'])
    header = np.rec.fromfile(data_file, dtype=header_dtype, shape=())
    return header


def update_header_from_data(header, data, is_image_stack=False):
    """Update the given MRC file header from the given data array.

    If the data is 3-dimensional, the header will be set to indicate that the
    file contains volume data unless is_image_stack is set to True.

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
        header: The header to update, as a numpy record array. The header is
            updated in-place.
        data: A numpy array containing the data.
        is_image_stack: A flag to indicate that three-dimensional data is an
            image stack, not a volume. If the data array is not three-
            dimensional, this flag is ignored.
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
        if is_image_stack:
            # Image stack. Space group 0, mz = 1, nz = sections in the volume
            header.ispg = IMAGE_STACK_SPACEGROUP
            header.mz = 1
            header.nz = shape[0]
        else:
            # Volume by default. Space group 1, nz = mz = sections in the volume
            header.ispg = VOLUME_SPACEGROUP
            header.nz = header.mz = shape[0]
    elif axes == 4:
        # Volume stack. Space group 401, mz = secs per vol, nz = total sections
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

    # Use a float64 accumulator to calculate mean and std deviation
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
