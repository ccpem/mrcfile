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
    
    """An object which represents an MRC / CCP4 map file.
    
    The header and data of the file are presented as numpy arrays.
    
    Usage: TODO:
    
    """
    
    def __init__(self, name, mode='r', overwrite=False, **kwargs):
        super(MrcFile, self).__init__(**kwargs)
        
        if mode not in ['r', 'r+', 'w+']:
            raise ValueError("Mode '{0}' not supported".format(mode))
        
        if ('w' in mode and os.path.exists(name) and not overwrite):
            raise IOError("File '{0}' already exists; set overwrite=True "
                          "to overwrite it".format(name))
        
        self._mode = mode
        self._read_only = (self._mode == 'r')
        
        self._open_file(name)
        
        try:
            if 'w' in mode:
                self._create_default_fields()
            else:
                self._read_stream()
                # TODO: add warning if file is too long?
        except Exception:
            self._close_file()
            raise
    
    def __repr__(self):
        return "MrcFile('{0}', mode='{1}')".format(self._iostream.name,
                                                   self._mode)
    
    def _open_file(self, name):
        """Open a file object to use as the I/O stream."""
        self._iostream = open(name, self._mode + 'b')
    
    def _read_stream(self):
        """Override _read_stream() to move back to start of file first."""
        self._iostream.seek(0)
        super(MrcFile, self)._read_stream()
        # TODO: add warning if file is larger than expected?
    
    def close(self):
        """Flush any changes to disk and close the file.
        
        This override calls super() to ensure the stream is flushed and closed,
        then closes the file object.
        """
        super(MrcFile, self).close()
        self._close_file()
    
    def _close_file(self):
        """Close the file object."""
        self._iostream.close()
