# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
gzipmrcfile
-----------

Module which exports the :class:`GzipMrcFile` class.

Classes:
    :class:`GzipMrcFile`: An object which represents a gzipped MRC file.

"""

from __future__ import annotations

import gzip
import os

from .mrcfile import MrcFile


class GzipMrcFile(MrcFile):
    """:class:`~mrcfile.mrcfile.MrcFile` subclass for handling gzipped files.

    Usage is the same as for :class:`~mrcfile.mrcfile.MrcFile`.

    """

    def __repr__(self) -> str:
        """Return a string representation of the GzipMrcFile object."""
        return f"GzipMrcFile('{self._fileobj.name}', mode='{self._mode}')"

    def _open_file(self, name: str | os.PathLike[str]) -> None:
        """Override _open_file() to open both normal and gzip files."""
        self._fileobj = open(name, self._mode + "b")  # noqa: SIM115
        self._iostream = gzip.GzipFile(fileobj=self._fileobj, mode="rb")

    def _close_file(self) -> None:
        """Override _close_file() to close both normal and gzip files."""
        self._iostream.close()
        self._fileobj.close()

    def _read(self, *, header_only: bool = False) -> None:
        """Override _read() to ensure gzip file is in read mode."""
        self._ensure_readable_gzip_stream()
        super()._read(header_only=header_only)

    def _ensure_readable_gzip_stream(self) -> None:
        """Make sure _iostream is a gzip stream that can be read."""
        if self._iostream.mode != gzip.READ:
            self._iostream.close()
            self._fileobj.seek(0)
            self._iostream = gzip.GzipFile(fileobj=self._fileobj, mode="rb")

    def _get_file_size(self) -> int:
        """Override _get_file_size() to avoid seeking from end."""
        self._ensure_readable_gzip_stream()
        pos = self._iostream.tell()
        extra = len(self._iostream.read())
        self._iostream.seek(pos, os.SEEK_SET)
        return pos + extra

    def flush(self) -> None:
        """Override :meth:`~mrcfile.mrcinterpreter.MrcInterpreter.flush` since
        GzipFile objects need special handling.
        """
        if not self._read_only:
            self._iostream.close()
            self._fileobj.seek(0)
            self._iostream = gzip.GzipFile(fileobj=self._fileobj, mode="wb")

            # Arrays converted to bytes so gzip can calculate sizes correctly
            self._iostream.write(self.header.tobytes())
            self._iostream.write(self.extended_header.tobytes())
            self._iostream.write(self.data.tobytes())
            self._iostream.flush()
            self._fileobj.truncate()
