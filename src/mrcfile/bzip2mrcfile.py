# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
bzip2mrcfile
------------

Module which exports the :class:`Bzip2MrcFile` class.

Classes:
    :class:`Bzip2MrcFile`: An object which represents a bzip2-compressed MRC
    file.

"""

from __future__ import annotations

import bz2
import os

from .mrcfile import MrcFile


class Bzip2MrcFile(MrcFile):
    """:class:`~mrcfile.mrcfile.MrcFile` subclass for handling bzip2-compressed
    files.

    Usage is the same as for :class:`~mrcfile.mrcfile.MrcFile`.

    """

    def __repr__(self) -> str:
        """Return a string representation of the Bzip2MrcFile object."""
        return f"Bzip2MrcFile('{self._fname}', mode='{self._mode}')"

    def _open_file(self, name: str | os.PathLike[str]) -> None:
        """Override _open_file() to open a bzip2 file."""
        self._fname = name
        if "w" in self._mode and not os.path.exists(name):
            open(name, mode="w").close()
        self._iostream = bz2.BZ2File(name, mode="r")  # type: ignore[assignment]  # awkward IO types

    def _read(self, *, header_only: bool = False) -> None:
        """Override _read() to ensure bzip2 file is in read mode."""
        self._ensure_readable_bzip2_stream()
        super()._read(header_only=header_only)

    def _ensure_readable_bzip2_stream(self) -> None:
        """Make sure _iostream is a bzip2 stream that can be read."""
        if self._iostream is None:
            raise RuntimeError("Cannot read file because no file is set")
        if not self._iostream.readable():
            self._iostream.close()
            self._iostream = bz2.BZ2File(self._fname, mode="r")  # type: ignore[assignment]  # awkward IO types

    def _get_file_size(self) -> int:
        """Override _get_file_size() to ensure stream is readable first."""
        if self._iostream is None:
            raise RuntimeError("Cannot get file size because no file is set")
        self._ensure_readable_bzip2_stream()
        return super()._get_file_size()

    def flush(self) -> None:
        """Override :meth:`~mrcfile.mrcinterpreter.MrcInterpreter.flush` since
        BZ2File objects need special handling.
        """
        if not self._read_only and self._iostream is not None:
            self._iostream.close()
            self._iostream = bz2.BZ2File(self._fname, mode="w")  # type: ignore[assignment]  # awkward IO types

            # Arrays converted to bytes so bz2 can calculate sizes correctly
            if self.header is not None:
                self._iostream.write(self.header.tobytes())
            if self.extended_header is not None:
                self._iostream.write(self.extended_header.tobytes())
            if self.data is not None:
                self._iostream.write(self.data.tobytes())
            # no equivalent for flush() with BZ2File
