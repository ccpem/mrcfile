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

from . import test_mrcfile
from mrcfile.gzipmrcfile import GzipMrcFile


class GzipMrcFileTest(test_mrcfile.MrcFileTest):
    
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
        self.fei1_ext_header_mrc_name = os.path.join(self.test_data, 'fei-extended.mrc.gz')
        self.fei2_ext_header_mrc_name = os.path.join(self.test_data, 'epu2.9_example.mrc.gz')

        # Create .gz files from .mrc files if necessary
        if not os.path.isfile(self.fei1_ext_header_mrc_name):
            print("Test data file fei-extended.mrc.gz not found. Creating a new copy...")
            fei1_ext_header_mrc_name = os.path.join(self.test_data, 'fei-extended.mrc')
            import gzip
            with open(fei1_ext_header_mrc_name, "rb") as mrc:
                with gzip.open(self.fei1_ext_header_mrc_name, 'wb') as gzipf:
                    gzipf.write(mrc.read())

        if not os.path.isfile(self.fei2_ext_header_mrc_name):
            print("Test data file epu2.9_example.mrc.gz not found. Creating a new copy...")
            fei2_ext_header_mrc_name = os.path.join(self.test_data, 'epu2.9_example.mrc')
            import gzip
            with open(fei2_ext_header_mrc_name, "rb") as mrc:
                with gzip.open(self.fei2_ext_header_mrc_name, 'wb') as gzipf:
                    gzipf.write(mrc.read())

        # Set the newmrc method to the GzipMrcFile constructor
        self.newmrc = GzipMrcFile
        
        # Set up parameters so MrcObject tests run on the GzipMrcFile class
        obj_mrc_name = os.path.join(self.test_output, 'test_mrcobject.mrc')
        self.mrcobject = GzipMrcFile(obj_mrc_name, 'w+', overwrite=True)
        # Flush and re-read to ensure underlying file is valid gzip
        self.mrcobject.flush()
        self.mrcobject._read()
    
    def test_non_mrc_file_is_rejected(self):
        """Override test to change expected error message."""
        name = os.path.join(self.test_data, 'emd_3197.png')
        with (self.assertRaisesRegex(IOError, 'Not a gzipped file')):
            GzipMrcFile(name)
    
    def test_non_mrc_file_gives_correct_warnings_in_permissive_mode(self):
        """Override test - permissive mode still can't read non-gzip files."""
        name = os.path.join(self.test_data, 'emd_3197.png')
        with (self.assertRaisesRegex(IOError, 'Not a gzipped file')):
            GzipMrcFile(name, permissive=True)
    
    def test_repr(self):
        """Override test to change expected repr string."""
        with GzipMrcFile(self.example_mrc_name) as mrc:
            assert repr(mrc) == "GzipMrcFile('{0}', mode='r')".format(self.example_mrc_name)


if __name__ == "__main__":
    unittest.main()
