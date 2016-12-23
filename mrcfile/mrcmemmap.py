# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
mrcmemmap
---------

TODO: this module is currently broken - do not use!

"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os

import numpy as np

import mrcfile.utils as utils
from .mrcinterpreter import MrcInterpreter


class MrcMemmap(MrcInterpreter):
    
    """TODO:
    
    """
    
    def set_extended_header(self, extended_header):
        """Replace the file's extended header.
        
        Note that the file's entire data block must be moved if the extended
        header size changes. Setting a new extended header can therefore be
        very time consuming with large files, if the new extended header
        occupies a different number of bytes than the previous one.
        """
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
    
    def set_data(self, data):
        """TODO: doc Get the file's current data block as a numpy array.
        
        The data is opened as a memory map to the file on disk, meaning that
        slices of data will be fetched from disk only when requested. This
        allows parts of very large files to be accessed easily and quickly.
        
        The data values can be modified and will be written to disk when the
        file is closed (unless the file is open in read-only mode). However,
        after changing any values the header statistics might be incorrect. Call
        update_header_stats() to update them if required -- this is usually a
        good idea, but can take a long time for large files.
        
        Returns:
            The file's data block, as a numpy array.
        """
        """Replace the file's data.
        
        This replaces the current data with a copy of the given array, and
        updates the header to match the new data dimensions. The data statistics
        (min, max, mean and rms) stored in the header will also be updated.
        """
        if self._read_only:
            raise ValueError('This file is read-only')
        
        # Copy the header and update it from the data
        # We use a copy so the current header and data will remain unchanged
        # if the new data is invalid and an exception is raised
        new_header = self.header.copy()
        utils.update_header_from_data(new_header, data)
        if data.size > 0:
            utils.update_header_stats(new_header, data)
        else:
            utils.reset_header_stats(new_header)
        
        # The dtype of the new memmap array might not be the same as the given
        # data array. For example if an array of unsigned bytes is given, they
        # should be written in mode 6 as unsigned 16-bit ints to avoid data
        # loss. So, we construct a new dtype to use for the file's data array.
        mode = new_header.mode
        dtype = utils.dtype_from_mode(mode).newbyteorder(mode.dtype.byteorder)
        
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
    
    def _read_data(self):
        """Read the data block from the file.
        
        This method first calculates the parameters needed to read the data
        (block start position, endian-ness, file mode, array shape) and then
        opens the data as a numpy memmap array.
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
        elif ispg == utils.IMAGE_STACK_SPACEGROUP and nz == 1:
            # Use a 2D array for a single image
            shape = (ny, nx)
        else:
            shape = (nz, ny, nx)
            
        header_size = self.header.nbytes + self.header.nsymbt
        data_size = nx * ny * nz * dtype.itemsize
        
        self._file.seek(0, os.SEEK_END)
        file_size = self._file.tell()
        assert file_size == header_size + data_size
        
        self._open_memmap(dtype, shape)
    
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
