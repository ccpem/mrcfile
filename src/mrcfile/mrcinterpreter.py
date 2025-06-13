# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
mrcinterpreter
--------------

Module which exports the :class:`MrcInterpreter` class.

Classes:
    :class:`MrcInterpreter`: An object which can interpret an I/O stream as MRC
    data.

"""

from __future__ import annotations

import warnings
from contextlib import suppress
from typing import BinaryIO

import numpy as np

from . import utils
from .constants import MAP_ID
from .dtypes import HEADER_DTYPE
from .mrcobject import MrcObject


class MrcInterpreter(MrcObject):
    """An object which interprets an I/O stream as MRC / CCP4 map data.

    The header and data are handled as numpy arrays - see
    :class:`~mrcfile.mrcobject.MrcObject` for details.

    :class:`MrcInterpreter` can be used directly, but it is mostly intended as
    a superclass to provide common stream-handling functionality. This can be
    used by subclasses which will handle opening and closing the stream.

    This class implements the :meth:`~object.__enter__` and
    :meth:`~object.__exit__` special methods which allow it to be used by the
    Python context manager in a :keyword:`with` block. This ensures that
    :meth:`close` is called after the object is finished with.

    When reading the I/O stream, a :exc:`ValueError` is raised if the data is
    invalid in one of the following ways:

    #. The header's ``map`` field is not set correctly to confirm the file
       type.
    #. The machine stamp is invalid and so the data's byte order cannot be
       determined.
    #. The mode number is not recognised. Currently accepted modes are 0, 1, 2,
       4 and 6.
    #. The file is not large enough for the specified extended header size.
    #. The data block is not large enough for the specified data type and
       dimensions.

    :class:`MrcInterpreter` offers a permissive read mode for handling
    problematic files. If ``permissive`` is set to :data:`True` and any of the
    validity checks fails, a :mod:`warning <warnings>` is issued instead of an
    exception, and file interpretation continues. If the mode number is invalid
    or the data block is too small, the
    :attr:`~mrcfile.mrcobject.MrcObject.data` attribute will be set to
    :data:`None`. In this case, it might be possible to inspect and correct the
    header, and then call :meth:`_read` again to read the data correctly. See
    the :doc:`usage guide <../usage_guide>` for more details.

    Methods:

    * :meth:`flush`
    * :meth:`close`

    Methods relevant to subclasses:

    * :meth:`_read`
    * :meth:`_read_data`
    * :meth:`_read_bytearray_from_stream`

    """

    def __init__(
        self,
        iostream: BinaryIO | None = None,
        *,
        permissive: bool = False,
        header_only: bool = False,
    ):
        """Initialise a new MrcInterpreter object.

        This initialiser reads the stream if it is given. In general,
        subclasses should call :meth:`__init__` without giving an ``iostream``
        argument, then set the ``_iostream`` attribute themselves and call
        :meth:`_read` when ready.

        To use the MrcInterpreter class directly, pass a stream when creating
        the object (or for a write-only stream, create an MrcInterpreter with
        no stream, call :meth:`._create_default_attributes` and set the
        ``_iostream`` attribute directly).

        Args:
            iostream: The I/O stream to use to read and write MRC data. The
                default is :data:`None`.
            permissive: Read the stream in permissive mode. The default is
                :data:`False`.
            header_only: Only read the header (and extended header) from the
                file. The default is :data:`False`.

        Raises:
            :exc:`ValueError`: If ``iostream`` is given, the data it contains
                cannot be interpreted as a valid MRC file and ``permissive``
                is :data:`False`.

        Warns:
            RuntimeWarning: If ``iostream`` is given, the data it contains
                cannot be interpreted as a valid MRC file and ``permissive``
                is :data:`True`.
        """
        super().__init__()

        self._iostream = iostream
        self._permissive = permissive

        # If iostream is given, initialise by reading it
        if self._iostream is not None:
            self._read(header_only=header_only)

    def __enter__(self) -> MrcInterpreter:
        """Called by the context manager at the start of a :keyword:`with`
        block.

        Returns:
            This object (``self``).
        """
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Called by the context manager at the end of a :keyword:`with`
        block.

        This ensures that the :meth:`close` method is called.
        """
        self.close()

    def __del__(self) -> None:
        """Attempt to flush the stream when this object is garbage collected.

        It's better not to rely on this - instead, use a :keyword:`with`
        block or explicitly call the :meth:`close` method.
        """
        with suppress(Exception):
            self.close()

    def _read(self, *, header_only: bool = False) -> None:
        """Read the header, extended header and data from the I/O stream.

        Before calling this method, the stream should be open and positioned at
        the start of the header. This method will advance the stream to the end
        of the data block (or the end of the extended header if ``header_only``
        is :data:`True`.

        Args:
            header_only: Only read the header and extended header from the
                stream. The default is :data:`False`.

        Raises:
            :exc:`ValueError`: If the data in the stream cannot be interpreted
                 as a valid MRC file and ``permissive`` is :data:`False`.

        Warns:
            RuntimeWarning:  If the data in the stream cannot be interpreted
                 as a valid MRC file and ``permissive`` is :data:`True`.
        """
        self._read_header()
        self._read_extended_header()
        if not header_only:
            self._read_data()

    def _read_header(self) -> None:
        """Read the MRC header from the I/O stream.

        The header will be read from the current stream position, and the
        stream will be advanced by 1024 bytes.

        Raises:
            :exc:`ValueError`: If no stream has been set.
            :exc:`ValueError`: If the data in the stream cannot be interpreted
                 as a valid MRC file and ``permissive`` is :data:`False`.

        Warns:
            RuntimeWarning:  If the data in the stream cannot be interpreted
                 as a valid MRC file and ``permissive`` is :data:`True`.
        """
        # Read 1024 bytes from the stream
        header_arr, bytes_read = self._read_bytearray_from_stream(HEADER_DTYPE.itemsize)
        if bytes_read < HEADER_DTYPE.itemsize:
            raise ValueError("Couldn't read enough bytes for MRC header")

        # Use a recarray to allow access to fields as attributes
        # (e.g. header.mode instead of header['mode'])
        header = (
            np.frombuffer(header_arr, dtype=HEADER_DTYPE).reshape(()).view(np.recarray)
        )

        # Check the map ID to make sure this is an MRC file. The full map ID
        # should be 'MAP ', but we check only the first three bytes because
        # this is the form specified in the MRC2014 paper and is used by some
        # other software.
        if bytes(header.map)[:3] != MAP_ID[:3]:
            msg = "Map ID string not found - not an MRC file, or file is corrupt"
            if self._permissive:
                warnings.warn(msg, RuntimeWarning)
            else:
                raise ValueError(msg)

        # Read the machine stamp to get the file's byte order
        try:
            byte_order = utils.byte_order_from_machine_stamp(header.machst)
        except ValueError as err:
            if self._permissive:
                byte_order = "<"  # try little-endian as a sensible default
                warnings.warn(str(err), RuntimeWarning)
            else:
                raise

        # Create a new dtype with the correct byte order and update the header
        # Assigning to .dtype is discouraged but not yet deprecated, and none of the
        # other methods (view, astype) achieve quite what we need here
        header.dtype = header.dtype.newbyteorder(byte_order)  # type: ignore[misc]

        # Check mode is valid; if not, try the opposite byte order
        # (Some MRC files have been seen 'in the wild' that are correct except
        # that the machine stamp indicates the wrong byte order.)
        if self._permissive:
            try:
                utils.dtype_from_mode(header.mode)
            except ValueError:
                try:
                    opp_mode = header.mode.view(header.mode.dtype.newbyteorder())
                    utils.dtype_from_mode(opp_mode)
                    # If we get here the new byte order is probably correct
                    # Use it and issue a warning
                    # Assigning to .dtype is discouraged but not yet deprecated, and
                    # none of the other methods (view, astype) achieve quite what we
                    # need here
                    header.dtype = header.dtype.newbyteorder()  # type: ignore[misc]
                    pretty_machst = utils.pretty_machine_stamp(header.machst)
                    warnings.warn(
                        f"Machine stamp '{pretty_machst}' does not match the apparent"
                        f" byte order '{header.mode.dtype.byteorder}'",
                        RuntimeWarning,
                    )
                except ValueError:
                    # Neither byte order gives a valid mode. Ignore for now,
                    # and a warning will be issued by _read_data()
                    pass

        header.flags.writeable = not self._read_only
        self._header = header

    def _read_extended_header(self) -> None:
        """Read the extended header from the stream.

        If there is no extended header, a zero-length array is assigned to the
        extended_header attribute.

        The dtype is set as void (``'V1'``).

        Raises:
            :exc:`ValueError`: If no stream has been set.
            :exc:`ValueError`: If the stream is not long enough to contain the
                extended header indicated by the header and ``permissive``
                is :data:`False`.

        Warns:
            RuntimeWarning: If the stream is not long enough to contain the
                extended header indicated by the header and ``permissive``
                is :data:`True`.
        """
        if self.header is None:
            raise RuntimeError(
                "Cannot read extended header from an uninitialised or closed MRC object"
            )
        ext_header_arr, bytes_read = self._read_bytearray_from_stream(
            int(self.header.nsymbt)
        )

        if bytes_read < self.header.nsymbt:
            msg = (
                f"Expected {self.header.nsymbt} bytes in extended header but could only"
                f" read {bytes_read}"
            )
            if self._permissive:
                warnings.warn(msg, RuntimeWarning)
                self._extended_header = None
                return
            else:
                raise ValueError(msg)

        self._extended_header = np.frombuffer(ext_header_arr, dtype="V1")

        self._extended_header.flags.writeable = not self._read_only

    def _read_data(self) -> None:
        """Read the data array from the stream.

        This method uses information from the header to set the data array's
        shape and dtype.

        Raises:
            :exc:`ValueError`: If no stream has been set.
            :exc:`ValueError`: If the stream is not long enough to contain the
                data indicated by the header and ``permissive`` is
                :data:`False`.

        Warns:
            RuntimeWarning: If the stream is not long enough to contain the
                data indicated by the header and ``permissive`` is
                :data:`True`.
        """
        self._read_data_from_stream()

    def _read_data_from_stream(self, max_bytes: int = 0) -> None:
        """Read the data array from the stream.

        Unless you need to use the ``max_bytes`` argument, call ``_read_data`` instead.

        Args:
            max_bytes: Read at most this many bytes from the stream. If zero or
                negative, the full size of the data block as defined in the header
                will be read, even if this is very large.

        Raises:
            :exc:`ValueError`: If no stream has been set.
            :exc:`ValueError`: If the stream is not long enough to contain the
                data indicated by the header and ``permissive`` is
                :data:`False`.

        Warns:
            RuntimeWarning: If the stream is not long enough to contain the
                data indicated by the header and ``permissive`` is
                :data:`True`.
        """
        if self.header is None:
            raise RuntimeError(
                "Cannot read data from an uninitialised or closed MRC object"
            )

        try:
            dtype = utils.data_dtype_from_header(self.header)
        except ValueError as err:
            if self._permissive:
                warnings.warn(f"{err} - data block cannot be read", RuntimeWarning)
                self._data = None
                return
            else:
                raise

        shape = utils.data_shape_from_header(self.header)

        nbytes = dtype.itemsize
        for axis_length in shape:
            nbytes *= axis_length

        if max_bytes > 0 and nbytes > max_bytes:
            msg = f"Expected {nbytes} bytes in data block but limit is {max_bytes}"
            if self._permissive:
                warnings.warn(msg, RuntimeWarning)
                self._data = None
                return
            else:
                raise ValueError(msg)

        data_arr, bytes_read = self._read_bytearray_from_stream(nbytes)

        if bytes_read < nbytes:
            msg = (
                f"Expected {nbytes} bytes in data block but could only read"
                f" {bytes_read}"
            )
            if self._permissive:
                warnings.warn(msg, RuntimeWarning)
                self._data = None
                return
            else:
                raise ValueError(msg)

        self._data = np.frombuffer(data_arr, dtype=dtype).reshape(shape)
        self._data.flags.writeable = not self._read_only

    def _read_bytearray_from_stream(
        self, number_of_bytes: int
    ) -> tuple[bytearray, int]:
        """Read a :class:`bytearray` from the stream.

        This default implementation relies on the stream implementing the
        :meth:`~io.BufferedIOBase.readinto` method to avoid copying the new
        array while creating the mutable :class:`bytearray`. Subclasses
        should override this if their stream does not support
        :meth:`~io.BufferedIOBase.readinto`.

        Returns:
            A 2-tuple of the :class:`bytearray` and the number of bytes that
            were read from the stream.

        Raises:
            :exc:`ValueError`: If no stream has been set.
            :exc:`AttributeError`: If the stream does not support
                :meth:`~io.BufferedIOBase.readinto`.
        """
        if self._iostream is None:
            raise RuntimeError("Cannot read data because no iostream is set")
        result_array = bytearray(number_of_bytes)
        bytes_read = self._iostream.readinto(result_array)  # type: ignore[attr-defined]
        return result_array, bytes_read

    def close(self) -> None:
        """Flush to the stream and clear the header and data attributes."""
        if (
            self.header is not None
            and self._iostream is not None
            and not self._iostream.closed
        ):
            self.flush()
        self._header = None
        self._extended_header = None
        self._close_data()

    def flush(self) -> None:
        """Flush the header and data arrays to the I/O stream.

        This implementation seeks to the start of the stream, writes the
        header, extended header and data arrays, and then truncates the stream.

        Subclasses should override this implementation for streams which do not
        support :meth:`~io.IOBase.seek` or :meth:`~io.IOBase.truncate`.
        """
        if not self._read_only and self._iostream is not None:
            self._iostream.seek(0)
            self._iostream.write(self.header)  # type: ignore[arg-type, call-overload]  # https://github.com/numpy/numpy/issues/26783
            self._iostream.write(self.extended_header)  # type: ignore[arg-type, call-overload]  # https://github.com/numpy/numpy/issues/26783
            if self.data is not None:
                self._iostream.write(np.ascontiguousarray(self.data))  # type: ignore[arg-type, call-overload]  # https://github.com/numpy/numpy/issues/26783
            self._iostream.truncate()
            self._iostream.flush()
