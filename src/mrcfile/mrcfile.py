# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
mrcfile
-------

Module which exports the :class:`MrcFile` class.

Classes:
    :class:`MrcFile`: An object which represents an MRC file.

"""

from __future__ import annotations

import os
import warnings
from typing import Literal, TextIO

from .mrcinterpreter import MrcInterpreter


class MrcFile(MrcInterpreter):
    """An object which represents an MRC file.

    The header and data are handled as numpy arrays - see
    :class:`~mrcfile.mrcobject.MrcObject` for details.

    :class:`MrcFile` supports a permissive read mode for attempting to open
    corrupt or invalid files. See
    :class:`mrcfile.mrcinterpreter.MrcInterpreter` or the :doc:`usage guide
    <../usage_guide>` for more information.

    Usage:
        To create a new MrcFile object, pass a file name and optional mode. To
        ensure the file is written to disk and closed correctly, it's best to
        use the :keyword:`with` statement:

        >>> with MrcFile('tmp.mrc', 'w+') as mrc:
        ...     mrc.set_data(np.zeros((10, 10), dtype=np.int8))

        In mode ``r`` or ``r+``, the named file is opened from disk and read.
        In mode ``w+`` a new empty file is created and will be written to disk
        at the end of the :keyword:`with` block (or when
        :meth:`~.MrcInterpreter.flush` or :meth:`close` is called).

    """

    def __init__(
        self,
        name: str | os.PathLike[str],
        mode: Literal["r", "r+", "w+"] = "r",
        *,
        overwrite: bool = False,
        permissive: bool = False,
        header_only: bool = False,
    ) -> None:
        """Initialise a new :class:`MrcFile` object.

        The given file name is opened in the given mode. For mode ``r`` or
        ``r+`` the header, extended header and data are read from the file. For
        mode ``w+`` a new file is created with a default header and empty
        extended header and data arrays.

        Args:
            name: The file name to open, as a string or pathlib Path.
            mode: The file mode to use. This should be one of the following:
                ``r`` for read-only, ``r+`` for read and write, or ``w+`` for a
                new empty file. The default is ``r``.
            overwrite: Flag to force overwriting of an existing file if the
                mode is ``w+``. If :data:`False` and a file of the same name
                already exists, the file is not overwritten and an exception is
                raised. The default is :data:`False`.
            permissive: Read the file in permissive mode. (See
                :class:`mrcfile.mrcinterpreter.MrcInterpreter` for details.)
                The default is :data:`False`.
            header_only: Only read the header (and extended header) from the
                file. The default is :data:`False`.

        Raises:
            :exc:`ValueError`: If the mode is not one of ``r``, ``r+`` or
                ``w+``.
            :exc:`ValueError`: If the file is not a valid MRC file and
                ``permissive`` is :data:`False`.
            :exc:`ValueError`: If the mode is ``w+``, the file already exists
                and overwrite is :data:`False`.
            :exc:`OSError`: If the mode is ``r`` or ``r+`` and the file does
                not exist.

        Warns:
            RuntimeWarning: If the file appears to be a valid MRC file but the
                data block is longer than expected from the dimensions in the
                header.
            RuntimeWarning: If the file is not a valid MRC file and
                ``permissive`` is :data:`True`.
            RuntimeWarning: If the header's ``exttyp`` field is set to a known
                value but the extended header's size is not a multiple of the
                number of bytes in the corresponding dtype.
        """
        super().__init__(permissive=permissive)

        if mode not in ["r", "r+", "w+"]:
            raise ValueError(f"Mode '{mode}' not supported")

        name = str(name)  # in case name is a pathlib Path
        if "w" in mode and os.path.exists(name) and not overwrite:
            raise ValueError(
                f"File '{name}' already exists; set overwrite=True to overwrite it"
            )

        self._mode: Literal["r", "r+", "w+"] = mode
        self._read_only = self._mode == "r"

        self._open_file(name)

        try:
            if "w" in mode:
                self._create_default_attributes()
            else:
                self._read(header_only=header_only)
        except Exception:
            self._close_file()
            raise

    def __repr__(self) -> str:
        """Return a string representation of the MrcFile object."""
        name = getattr(self._iostream, "name", "<unnamed stream>")
        return f"MrcFile('{name}', mode='{self._mode}')"

    def _open_file(self, name: str | os.PathLike[str]) -> None:
        """Open a file object to use as the I/O stream."""
        binary_mode: Literal["rb", "r+b", "w+b"] = self._mode + "b"  # type: ignore[assignment]
        self._iostream = open(name, binary_mode)  # noqa: SIM115  # no context manager

    def _read(self, *, header_only: bool = False) -> None:
        """Override _read() to move back to start of file first."""
        if self._iostream is None:
            raise RuntimeError("Cannot read data because no file is set")
        self._iostream.seek(0)
        super()._read(header_only=header_only)

    def _read_data(self) -> None:
        """Read data array from file and check file size matches data block size."""
        if self.header is None:
            raise RuntimeError(
                "Cannot read data from an uninitialised or closed MRC object"
            )
        file_size = self._get_file_size()
        # Need to use self.header.nsymbt rather than self.extended_header.nbytes because
        # self.extended_header might be None in permissive read mode. Need to convert to
        # Python int (rather than numpy int32) to avoid possible overflow.
        header_size = self.header.nbytes + int(self.header.nsymbt)
        remaining_file_size = file_size - header_size

        super()._read_data_from_stream(max_bytes=remaining_file_size)

        # Check if the file is the expected size.
        if self.data is not None:
            data_size = self.data.nbytes
            if data_size < remaining_file_size:
                msg = (
                    f"MRC file is {remaining_file_size - data_size} bytes larger than"
                    " expected"
                )
                warnings.warn(msg, RuntimeWarning)

    def _get_file_size(self) -> int:
        """Return the size of the underlying file object, in bytes."""
        if self._iostream is None:
            raise RuntimeError("Cannot get file size because no file is set")
        pos = self._iostream.tell()
        self._iostream.seek(0, os.SEEK_END)
        size = self._iostream.tell()
        self._iostream.seek(pos, os.SEEK_SET)
        return size

    def close(self) -> None:
        """Flush any changes to disk and close the file.

        This override calls :meth:`.MrcInterpreter.close` to ensure the stream
        is flushed and closed, then closes the file object.
        """
        super().close()
        self._close_file()

    def _close_file(self) -> None:
        """Close the file object."""
        if self._iostream is None:
            raise RuntimeError("Cannot close file because no file is set")
        self._iostream.close()

    def validate(self, print_file: TextIO | None = None) -> bool:
        """Validate this MRC file.

        The tests are:

        #. MRC format ID string: The ``map`` field in the header should
           contain "MAP ".
        #. Machine stamp: The machine stamp should contain one of
           ``0x44 0x44 0x00 0x00``, ``0x44 0x41 0x00 0x00`` or
           ``0x11 0x11 0x00 0x00``.
        #. MRC mode: the ``mode`` field should be one of the supported mode
           numbers: 0, 1, 2, 4, 6 or 12. (Note that MRC modes 3 and 101 are
           also valid according to the MRC 2014 specification but are not
           supported by mrcfile.)
        #. Map and cell dimensions: The header fields ``nx``, ``ny``, ``nz``,
           ``mx``, ``my``, ``mz``, ``cella.x``, ``cella.y`` and ``cella.z``
           must all be positive numbers.
        #. Axis mapping: Header fields ``mapc``, ``mapr`` and ``maps`` must
           contain the values 1, 2, and 3 (in any order).
        #. Volume stack dimensions: If the spacegroup is in the range 401--630,
           representing a volume stack, the ``nz`` field should be exactly
           divisible by ``mz`` to represent the number of volumes in the stack.
        #. Header labels: The ``nlabl`` field should be set to indicate the
           number of labels in use, and the labels in use should appear first
           in the label array.
        #. MRC format version: The ``nversion`` field should be 20140 or 20141
           for compliance with the MRC2014 standard.
        #. Extended header type: If an extended header is present, the
           ``exttyp`` field should be set to indicate the type of extended
           header.
        #. Data statistics: The statistics in the header should be correct for
           the actual data in the file, or marked as undetermined.
        #. File size: The size of the file on disk should match the expected
           size calculated from the MRC header.

        Args:
            print_file: The output text stream to use for printing messages
                about the validation. This is passed directly to the ``file``
                argument of Python's :func:`print` function. The default is
                :data:`None`, which means output will be printed to
                :data:`sys.stdout`.

        Returns:
            :data:`True` if the file is valid, or :data:`False` if the file
            does not meet the MRC format specification in any way.
        """
        if self.header is None:
            raise RuntimeError("Cannot validate an uninitialised or closed MRC object")
        valid = super().validate(print_file=print_file)

        ext_header_nbytes = (
            self.extended_header.nbytes if self.extended_header is not None else 0
        )

        if self.data is not None:
            # Check file size
            file_size = self._get_file_size()
            mrc_size = self.header.nbytes + ext_header_nbytes + self.data.nbytes
            if file_size != mrc_size:
                print(
                    f"File is larger than expected. Actual size: {file_size} bytes; "
                    f"expected size: {mrc_size} bytes (calculated from header)",
                    file=print_file,
                )
                valid = False
        else:
            print(
                "Data block could not be read - file size not checked", file=print_file
            )
            valid = False

        return valid
