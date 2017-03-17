# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for compressedmrcfile.py
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import unittest

from .test_mrcfile import MrcFileTest
from mrcfile.compressedmrcfile import CompressedMrcFile


class CompressedMrcFileTest(MrcFileTest):
    
    """Unit tests for compressed MRC file I/O.
    
    Note that this test class inherits MrcFileTest to ensure all of the tests
    for MrcObject and MrcFile work correctly for the CompressedMrcFile subclass.
    
    """
    
    def setUp(self):
        # Set up as if for MrcFileTest
        super(CompressedMrcFileTest, self).setUp()
        
        # Replace test MRC files with their gzipped equivalents
        self.example_mrc_name = os.path.join(self.test_data, 'emd_3197.map.gz')
        self.ext_header_mrc_name = os.path.join(self.test_data, 'emd_3001.map.gz')
        
        # Set the newmrc method to the CompressedMrcFile constructor
        self.newmrc = CompressedMrcFile
        
        # Set up parameters so MrcObject tests run on the CompressedMrcFile class
        obj_mrc_name = os.path.join(self.test_output, 'test_mrcobject.mrc')
        self.mrcobject = CompressedMrcFile(obj_mrc_name, 'w+', overwrite=True)
        # Flush and re-read to ensure underlying file is valid gzip
        self.mrcobject.flush()
        self.mrcobject._read()
    
    def test_non_mrc_file_is_rejected(self):
        """Override test to change expected error message."""
        name = os.path.join(self.test_data, 'emd_3197.png')
        with (self.assertRaisesRegex(IOError, 'Not a gzipped file')):
            CompressedMrcFile(name)
    
    def test_non_mrc_file_gives_correct_warnings_in_permissive_mode(self):
        """Override test - permissive mode still can't read non-gzip files."""
        name = os.path.join(self.test_data, 'emd_3197.png')
        with (self.assertRaisesRegex(IOError, 'Not a gzipped file')):
            CompressedMrcFile(name)
    
    def test_repr(self):
        """Override test to change expected repr string."""
        with CompressedMrcFile(self.example_mrc_name) as mrc:
            assert repr(mrc) == ("CompressedMrcFile('{0}', mode='r', compression='gzip')"
                                 .format(self.example_mrc_name))


if __name__ == "__main__":
    unittest.main()
