# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
mrcmemmap
---------

Module which exports the :class:`MrcMemmap` class.

Classes:
    :class:`MrcMemmap`: An MrcFile subclass that uses a memory-mapped data
    array.

"""

from __future__ import annotations

import mmap
import os
import warnings

import numpy as np

from . import utils
from .mrcfile import MrcFile


class MrcMemmap(MrcFile):
    """MrcFile subclass that uses a :class:`numpy memmap array <numpy.memmap>`
    for the data.

    Using a memmap means that the disk access is done lazily: the data array
    will only be read or written in small chunks when required. To access the
    contents of the array, use the array slice operator.

    Usage is the same as for :class:`~mrcfile.mrcfile.MrcFile`.

    Note that memmap arrays use a fairly small chunk size and so performance
    could be poor on file systems that are optimised for infrequent large I/O
    operations.

    If required, it is possible to create a very large empty file by creating a
    new MrcMemmap and then calling :meth:`_open_memmap` to create the memmap
    array, which can then be filled slice-by-slice. Be aware that the contents
    of a new, empty memmap array depend on your platform: the data values
    could be garbage or zeros.

    """

    _data: np.memmap | None

    def __repr__(self) -> str:
        """Return a string representation of the MrcMemmap object."""
        name = getattr(self._iostream, "name", "<unnamed stream>")
        return f"MrcMemmap('{name}', mode='{self._mode}')"

    def set_extended_header(self, extended_header: np.ndarray) -> None:
        """Replace the file's extended header.

        Note that the file's entire data block must be moved if the extended
        header size changes. Setting a new extended header can therefore be
        very time consuming with large files, if the new extended header
        occupies a different number of bytes than the previous one.
        """
        if self.header is None or self._iostream is None:
            raise RuntimeError(
                "Cannot set extended header on an uninitialised or closed MRC object"
            )
        old_ext_header_size = (
            self.extended_header.nbytes if self.extended_header is not None else 0
        )
        super().set_extended_header(extended_header)
        if extended_header.nbytes != old_ext_header_size:
            if self._data is None:
                data_copy = None
                data_nbytes = 0
            else:
                data_copy = self._data.copy()
                data_nbytes = data_copy.nbytes
                self._close_data()

            self._extended_header = extended_header
            self.header.nsymbt = extended_header.nbytes
            header_nbytes = self.header.nbytes + extended_header.nbytes
            total_nbytes = header_nbytes + data_nbytes

            # Workaround for https://github.com/ccpem/mrcfile/issues/65
            if data_nbytes == 0 and total_nbytes % mmap.ALLOCATIONGRANULARITY == 0:
                # Add one extra byte here to avoid triggering mmap error
                total_nbytes += 1

            self._iostream.truncate(total_nbytes)

            if data_copy is not None:
                self._open_memmap(data_copy.dtype, data_copy.shape)
                if self._data is not None:
                    np.copyto(self._data, data_copy)

    def flush(self) -> None:
        """Flush the header and data arrays to the file buffer."""
        if not self._read_only and self._iostream is not None:
            self._iostream.seek(0)
            self._iostream.write(self.header)  # type: ignore[arg-type, call-overload]  # https://github.com/numpy/numpy/issues/26783
            self._iostream.write(self.extended_header)  # type: ignore[arg-type, call-overload]  # https://github.com/numpy/numpy/issues/26783

            if self._data is None:
                data_nbytes = 0
            else:
                # Flushing the file before the mmap makes the mmap flush faster
                self._iostream.flush()
                self._data.flush()
                data_nbytes = self._data.nbytes

            self._iostream.flush()

            # Seek to end of data block so stream is left in the same position
            # as normal
            self._iostream.seek(data_nbytes, os.SEEK_CUR)

    def _read_data(self) -> None:
        """Read the data block from the file.

        This method first calculates the parameters needed to read the data
        (block start position, endian-ness, file mode, array shape) and then
        opens the data as a numpy memmap array.
        """
        if self.header is None:
            raise RuntimeError(
                "Cannot read data from an uninitialised or closed MRC object"
            )
        try:
            dtype = utils.data_dtype_from_header(self.header)
        except ValueError as err:
            if self._permissive:
                warnings.warn(f"{err} - data block not read", RuntimeWarning)
                self._data = None
                return
            else:
                raise

        shape = utils.data_shape_from_header(self.header)

        self._open_memmap(dtype, shape)

    def _open_memmap(self, dtype: np.dtype, shape: tuple) -> None:
        """Open a new memmap array pointing at the file's data block."""
        if self.header is None or self._iostream is None:
            raise RuntimeError(
                "Cannot open memmap for an uninitialised or closed MRC object"
            )
        acc_mode = "r" if self._read_only else "r+"
        # Need to use self.header.nsymbt rather than self.extended_header.nbytes because
        # self.extended_header might be None in permissive read mode. Need to convert to
        # Python int (rather than numpy int32) to avoid possible overflow.
        header_nbytes = self.header.nbytes + int(self.header.nsymbt)

        self._iostream.flush()
        try:
            self._data = np.memmap(  # type: ignore[call-overload]
                self._iostream,  # type: ignore[arg-type]  # awkward IO types
                dtype=dtype,
                mode=acc_mode,
                offset=header_nbytes,
                shape=shape,
            )
        except Exception:
            if self._permissive:
                warnings.warn("Error opening memmap", RuntimeWarning)
                self._data = None
            else:
                raise

        # Check if the file is the expected size.
        if self.data is not None:
            file_size = self._get_file_size()
            remaining_file_size = file_size - header_nbytes
            data_size = self.data.nbytes

            # Workaround for https://github.com/ccpem/mrcfile/issues/65
            if data_size == 0 and header_nbytes % mmap.ALLOCATIONGRANULARITY == 0:
                # Expect a file one byte larger here to avoid triggering mmap error
                data_size = 1

            if data_size < remaining_file_size:
                msg = (
                    f"MRC file is {remaining_file_size - data_size} bytes larger than"
                    " expected"
                )
                warnings.warn(msg, RuntimeWarning)

    def _close_data(self) -> None:
        """Delete the existing memmap array, if it exists.

        The array is flagged as read-only before deletion, so if a reference to
        it has been kept elsewhere, changes to it should no longer be able to
        change the file contents.
        """
        if self._data is not None:
            self._data.flush()
            self._data.flags.writeable = False
            self._data = None

    def _set_new_data(self, data: np.ndarray) -> None:
        """Override of :meth:`_set_new_data` to handle opening a new memmap and
        copying data into it."""
        if self.header is None or self._iostream is None:
            raise RuntimeError(
                "Cannot set data on an uninitialised or closed MRC object"
            )
        # Need to use self.header.nsymbt rather than self.extended_header.nbytes because
        # self.extended_header might be None in permissive read mode. Need to convert to
        # Python int (rather than numpy int32) to avoid possible overflow.
        file_size = self.header.nbytes + int(self.header.nsymbt) + data.nbytes
        self._iostream.truncate(file_size)
        self._open_memmap(data.dtype, data.shape)
        if self._data is None:
            raise RuntimeError(
                "Cannot set data on an uninitialised or closed MRC object"
            )
        np.copyto(self._data, data, casting="no")
