# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.
"""
mrcfile
-------

Module which exports the MrcFile class.

Classes:
    MrcFile: An object which represents an MRC file.

"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import os

from .mrcinterpreter import MrcInterpreter


class MrcFile(MrcInterpreter):
    
    """An object which represents an MRC / CCP4 map file.
    
    The header and data are handled as numpy arrays - see MrcObject for details.
    
    Usage:
        To create a new MrcFile object, give a file name and optional mode. To
        ensure the file is written to disk and closed correctly, it's best to
        use the 'with' statement:
        
        >>> with MrcFile('tmp.mrc', 'w+') as mrc:
        >>>     mrc.set_data(np.zeros((10, 10), dtype=np.int8))
        
        In mode 'r' or 'r+', the named file is opened from disk and read. In
        mode 'w+' a new empty file is created and will be written to disk at the
        end of the 'with' block (or when flush() or close() is called).
    
    """
    
    def __init__(self, name, mode='r', overwrite=False, **kwargs):
        """Initialise a new MrcFile object.
        
        The given file name is opened in the given mode. For mode 'r' or 'r+'
        the header, extended header and data are read from the file. For mode
        'w+' a new file is created with a default header and empty extended
        header and data arrays.
        
        Args:
            name: The file name to open.
            mode: The file mode to use. This should be one of the following:
                'r' for read-only, 'r+' for read and write, or 'w+' for a new
                empty file. The default is 'r'.
            overwrite: Flag to force overwriting of an existing file if the mode
                is 'w+'. If False and a file of the same name already exists,
                the file is not overwritten and an exception is raised. The
                default is False.
        
        Raises:
            ValueError: The mode is not one of 'r', 'r+' or 'w+', or the file is
                not a valid MRC file.
            IOError: The mode is 'r' or 'r+' and the file does not exist, or the
                mode is 'w+', the file already exists and overwrite is False.
        """
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
                self._create_default_attributes()
            else:
                self._read_stream()
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
