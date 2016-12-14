# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
mrcfile
-------

TODO:

"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import os

from .mrcinterpreter import MrcInterpreter


def new(name, data=None, mrcmode=None, shape=None, overwrite=False):
    """Create a new MRC file."""
    mrc = MrcFile(name, mode='w+', overwrite=overwrite)
    if data is not None:
        mrc.set_data(data)
    return mrc


def read(name, mode='r'):
    # TODO: make this do something!
    pass


class MrcFile(MrcInterpreter):
    
    def __init__(self, name, mode='r', overwrite=False, **kwargs):
        if mode not in ['r', 'r+', 'w+']:
            raise ValueError("Mode '{0}' not supported".format(mode))
        
        if ('w' in mode and os.path.exists(name) and not overwrite):
            raise IOError("File '{0}' already exists; set overwrite=True"
                          "to overwrite it".format(name))
        
        self._mode = mode
        self._file = open(name, mode + 'b')
        
        self._read_only = (self._mode == 'r')
        
        try:
            super(MrcFile, self).__init__(**kwargs)
        except Exception:
            self._file.close()
            raise
    
    def __repr__(self):
        return "MrcFile('{0}', mode='{1}')".format(self._file.name,
                                                   self._file.mode[:-1])
    
    def close(self):
        """Flush any changes to disk and close the file."""
        if not self._file.closed:
            self.flush()
            self._file.close()
        super(MrcFile, self).close()
    
    def flush(self):
        """Flush the header and data arrays to the file buffer."""
        if not self._read_only:
            self._update_header_from_data()
            self._write_header()
            
            self._file.write(self.data)
            self._file.truncate()
            self._file.flush()
    
    def _write_header(self):
        self._file.seek(0)
        self._file.write(self.header)
        self._file.write(self.extended_header)
