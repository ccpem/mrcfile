# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for bzip2mrcfile.py
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import unittest

from .test_mrcfile import MrcFileTest
from mrcfile.bzip2mrcfile import Bzip2MrcFile


class Bzip2MrcFileTest(MrcFileTest):
    
    """Unit tests for bzip2 MRC file I/O.
    
    Note that this test class inherits MrcFileTest to ensure all of the tests
    for MrcObject and MrcFile work correctly for the Bzip2MrcFile subclass.
    
    """
    
    def setUp(self):
        # Set up as if for MrcFileTest
        super(Bzip2MrcFileTest, self).setUp()
        
        # Replace test MRC files with their gzipped equivalents
        self.example_mrc_name = os.path.join(self.test_data, 'EMD-3197.map.bz2')
        self.ext_header_mrc_name = os.path.join(self.test_data, 'EMD-3001.map.bz2')
        
        # Set the newmrc method to the GzipMrcFile constructor
        self.newmrc = Bzip2MrcFile
        
        # Set up parameters so MrcObject tests run on the GzipMrcFile class
        obj_mrc_name = os.path.join(self.test_output, 'test_mrcobject.mrc')
        self.mrcobject = Bzip2MrcFile(obj_mrc_name, 'w+', overwrite=True)
        # Flush and re-read to ensure underlying file is valid bzip2
        self.mrcobject.flush()
        self.mrcobject._read()
    
    def test_non_mrc_file_is_rejected(self):
        """Override test to change expected error message."""
        name = os.path.join(self.test_data, 'emd_3197.png')
        with (self.assertRaisesRegex(IOError, '[Ii]nvalid data stream')):
            Bzip2MrcFile(name)
    
    def test_non_mrc_file_gives_correct_warnings_in_permissive_mode(self):
        """Override test - permissive mode still can't read non-bzip2 files."""
        name = os.path.join(self.test_data, 'emd_3197.png')
        with (self.assertRaisesRegex(IOError, '[Ii]nvalid data stream')):
            Bzip2MrcFile(name, permissive=True)
    
    def test_repr(self):
        """Override test to change expected repr string."""
        with Bzip2MrcFile(self.example_mrc_name) as mrc:
            assert repr(mrc) == "Bzip2MrcFile('{0}', mode='r')".format(self.example_mrc_name)


if __name__ == "__main__":
    unittest.main()
