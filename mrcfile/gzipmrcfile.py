# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
gzipmrcfile
-----------

Module which exports the GzipMrcFile class.

Classes:
    GzipMrcFile: An object which represents a gzipped MRC file.

"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import gzip

from .mrcfile import MrcFile


class GzipMrcFile(MrcFile):
    
    """MrcFile subclass for handling gzipped files.
    
    Usage is the same as for MrcFile.
    
    """
    
    def __repr__(self):
        return "GzipMrcFile('{0}', mode='{1}')".format(self._fileobj.name,
                                                       self._mode)
    
    def _open_file(self, name):
        """Override _open_file() to open both normal and gzip files."""
        self._fileobj = open(name, self._mode + 'b')
        self._iostream = gzip.GzipFile(fileobj=self._fileobj, mode='rb')
    
    def _close_file(self):
        """Override _close_file() to close both normal and gzip files."""
        self._iostream.close()
        self._fileobj.close()
    
    def _read_stream(self):
        """Override _read_stream() to ensure gzip file is in read mode."""
        if self._iostream.mode != gzip.READ:
            self._iostream.close()
            self._fileobj.seek(0)
            self._iostream = gzip.GzipFile(fileobj=self._fileobj, mode='rb')
        super(GzipMrcFile, self)._read_stream()
    
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

