# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for gzipmrcfile.py
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import unittest

from mrcfile.gzipmrcfile import GzipMrcFile
from tests.test_mrcfile import MrcFileTest


class GzipMrcFileTest(MrcFileTest):
    
    """Unit tests for gzipped MRC file I/O.
    
    Note that this test class inherits MrcFileTest to ensure all of the tests
    for MrcObject and MrcFile work correctly for the GzipMrcFile subclass.
    
    """
    
    def setUp(self):
        # Set up as if for MrcFileTest
        super(GzipMrcFileTest, self).setUp()
        
        # Replace test MRC files with their gzipped equivalents
        self.example_mrc_name = os.path.join(self.test_data, 'emd_3197.map.gz')
        self.ext_header_mrc_name = os.path.join(self.test_data, 'emd_3001.map.gz')
        
        # Set the newmrc method to the GzipMrcFile constructor
        self.newmrc = GzipMrcFile
    
    def test_non_mrc_file_is_rejected(self):
        """Override test to change expected error message."""
        name = os.path.join(self.test_data, 'emd_3197.png')
        with (self.assertRaisesRegexp(IOError, 'Not a gzipped file')):
            with GzipMrcFile(name):
                pass
    
    def test_repr(self):
        """Override test to change expected repr string."""
        with GzipMrcFile(self.example_mrc_name) as mrc:
            assert repr(mrc) == "GzipMrcFile('{0}', mode='r')".format(self.example_mrc_name)

if __name__ == "__main__":
    unittest.main()
