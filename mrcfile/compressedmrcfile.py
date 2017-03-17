# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
compressedmrcfile
-----------------

Module which exports the :class:`CompressedMrcFile` class.

Classes:
    :class:`CompressedMrcFile`: An object which represents a gzipped MRC file.

"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import gzip

from .mrcfile import MrcFile


class CompressedMrcFile(MrcFile):
    
    """:class:`~mrcfile.mrcfile.MrcFile` subclass for handling compressed files.
    
    Usage is the same as for :class:`~mrcfile.mrcfile.MrcFile`, with optional
    additional arguments for the compression algorithm to be used.
    
    """
    
    def __init__(self, name, mode='r', compression='gzip', compresslevel=9, **kwargs):
        super(CompressedMrcFile, self).__init__(name, mode=mode, **kwargs)
        self.compression = compression
        self.compresslevel= compresslevel
    
    def __repr__(self):
        return ("CompressedMrcFile('{0}', mode='{1}', compression='{2}')"
                .format(self._fileobj.name, self._mode, self.compression))
    
    def _open_file(self, name):
        """Override _open_file() to open both normal and compressed files."""
        self._fileobj = open(name, self._mode + 'b')
        self._iostream = gzip.GzipFile(fileobj=self._fileobj, mode='rb')
    
    def _close_file(self):
        """Override _close_file() to close both normal and compressed files."""
        self._iostream.close()
        self._fileobj.close()
    
    def _read(self):
        """Override _read() to ensure compressed file is in read mode."""
        self._ensure_readable_stream()
        super(CompressedMrcFile, self)._read()
    
    def _ensure_readable_stream(self):
        """Make sure _iostream is a compressed stream that can be read."""
        if self._iostream.mode != gzip.READ:
            self._iostream.close()
            self._fileobj.seek(0)
            self._iostream = gzip.GzipFile(fileobj=self._fileobj, mode='rb')
    
    def _get_file_size(self):
        """Override _get_file_size() to avoid seeking from end."""
        self._ensure_readable_stream()
        pos = self._iostream.tell()
        extra = len(self._iostream.read())
        return pos + extra
    
    def flush(self):
        """Override flush() since GzipFile objects need special handling."""
        if not self._read_only:
            self._iostream.close()
            self._fileobj.seek(0)
            self._iostream = gzip.GzipFile(fileobj=self._fileobj, mode='wb')
            
            # Arrays converted to bytes so gzip can calculate sizes correctly
            self._iostream.write(self.header.tobytes())
            self._iostream.write(self.extended_header.tobytes())
            self._iostream.write(self.data.tobytes())
            self._iostream.flush()
            self._fileobj.truncate()
