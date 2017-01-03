# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
mrcinterpreter
--------------

TODO:

"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import numpy as np

from . import utils
from .dtypes import HEADER_DTYPE
from .mrcobject import MrcObject
from .constants import MAP_ID, IMAGE_STACK_SPACEGROUP


# Constants
MAP_ID_OFFSET_BYTES = 208  # location of 'MAP ' string in an MRC file


class MrcInterpreter(MrcObject):
    
    """An object which interprets an I/O stream as MRC / CCP4 map data.
    
    The header and data are handled as numpy arrays - see MrcObject for details.
    
    Subclasses or client code should handle opening and closing the I/O stream.
    
    """
    
    def __init__(self, iostream=None, **kwargs):
        super(MrcInterpreter, self).__init__(**kwargs)
        
        # Initialise iostream if given
        self._iostream = iostream
    
    def __enter__(self):
        """Called by the context manager at the start of a 'with' block.
        
        Returns:
            This object (self).
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called by the context manager at the end of a 'with' block.
        
        This ensures that the close() method is called.
        """
        self.close()
    
    def __del__(self):
        """Attempt to flush the stream when this object is garbage collected.
        
        It's better not to rely on this - instead, use a 'with' block or
        explicitly call the close() method.
        """
        try:
            self.close()
        except Exception:
            pass
    
    def _read_stream(self):
        """Read the header, extended header and data.
        
        Before calling this method, the stream should be open and positioned at
        the start of the header. This method will advance the stream to the end
        of the data block.
        """
        self._read_header()
        self._read_extended_header()
        self._read_data()

    def _read_header(self):
        """Read the MRC header from the I/O stream.
        
        The header will be read from the current stream position, and the stream
        will be advanced by 1024 bytes.
        
        Raises:
            ValueError: The file is not a valid MRC file.
        """
        # Read 1024 bytes from the stream
        header_str = self._iostream.read(HEADER_DTYPE.itemsize)
        
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
            pretty_bytes = ' '.join('0x{:02x}'.format(byte) for byte in machst)
            raise ValueError('Unrecognised machine stamp: ' + pretty_bytes)
        
        # Create a new dtype with the correct byte order and update the header
        header.dtype = header.dtype.newbyteorder(byte_order)
        
        header.flags.writeable = not self._read_only
        self._header = header
    
    def _read_extended_header(self):
        """Read the extended header from the stream.
        
        If there is no extended header, a zero-length array is assigned to the
        extended_header field.
        """
        ext_header_str = self._iostream.read(self.header.nsymbt)
        self._extended_header = np.fromstring(ext_header_str, dtype='V1')
        self._extended_header.flags.writeable = not self._read_only
    
    def _read_data(self):
        """Read the data block from the stream.
        
        This method uses information from the header to set the data array's
        shape and dtype correctly.
        """
        mode = self.header.mode
        dtype = utils.dtype_from_mode(mode).newbyteorder(mode.dtype.byteorder)
        
        # convert data dimensions from header into array shape
        nx = self.header.nx
        ny = self.header.ny
        nz = self.header.nz
        mz = self.header.mz
        ispg = self.header.ispg
        
        if utils.spacegroup_is_volume_stack(ispg):
            shape = (nz // mz, mz, ny, nx)
        elif ispg == IMAGE_STACK_SPACEGROUP and nz == 1:
            # Use a 2D array for a single image
            shape = (ny, nx)
        else:
            shape = (nz, ny, nx)
        
        nbytes = nx * ny * nz * dtype.itemsize
        data_str = self._iostream.read(nbytes)
        self._data = np.fromstring(data_str, dtype=dtype).reshape(shape)
        self._data.flags.writeable = not self._read_only
    
    def close(self):
        """Flush any changes to the stream and clear the data fields.
        """
        if self._header is not None and not self._iostream.closed:
            self.flush()
        self._header = None
        self._extended_header = None
        self._close_data()
    
    def flush(self):
        """Flush the header and data arrays to the I/O stream.
        
        This implementation seeks to the start of the stream, writes the header,
        extended header and data arrays, and then truncates the stream.
        
        Subclasses should override this implementation for streams which do not
        support seek() or truncate().
        """
        if not self._read_only:
            self._iostream.seek(0)
            self._iostream.write(self.header)
            self._iostream.write(self.extended_header)
            self._iostream.write(self.data)
            self._iostream.truncate()
            self._iostream.flush()
