# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for mrcmemmap.py
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import unittest

import numpy as np

from .test_mrcfile import MrcFileTest
from mrcfile.mrcmemmap import MrcMemmap


class MrcMemmapTest(MrcFileTest):
    
    """Unit tests for MRC file I/O with memory-mapped files.
    
    Note that this test class inherits MrcFileTest to ensure all of the tests
    for MrcObject and MrcFile work correctly for the MrcMemmap subclass.
    
    """
    
    def setUp(self):
        # Set up as if for MrcFileTest
        super(MrcMemmapTest, self).setUp()
        
        # Set the newmrc method to the MrcMemmap constructor
        self.newmrc = MrcMemmap
        
        # Set up parameters so MrcObject tests run on the MrcMemmap class
        obj_mrc_name = os.path.join(self.test_output, 'test_mrcobject.mrc')
        self.mrcobject = MrcMemmap(obj_mrc_name, 'w+', overwrite=True)
    
    def test_repr(self):
        """Override test to change expected repr string."""
        with MrcMemmap(self.example_mrc_name) as mrc:
            assert repr(mrc) == "MrcMemmap('{0}', mode='r')".format(self.example_mrc_name)
    
    def test_exception_raised_if_file_is_too_small_for_reading_data(self):
        """Override test to change expected error message."""
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(24, dtype=np.int16).reshape(2, 3, 4))
            assert mrc.header.mz == 2
            mrc.header.mz = mrc.header.nz = 3
        # The exception type and message are different on Linux and Windows
        expected_error_msg = ("mmap length is greater than file size"
                              "|Not enough storage is available"
                              "|Not enough memory resources are available")
        with self.assertRaisesRegex(Exception, expected_error_msg):
            self.newmrc(self.temp_mrc_name)
    
    def test_data_is_not_copied_unnecessarily(self):
        """Override test because data has to be copied for mmap."""
        data = np.arange(6, dtype=np.int16).reshape(1, 2, 3)
        self.mrcobject.set_data(data)
        assert self.mrcobject.data is not data
    
    def test_data_array_cannot_be_changed_after_closing_file(self):
        mrc = self.newmrc(self.temp_mrc_name, mode='w+')
        mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        data_ref = mrc.data
        # Check that writing to the data array does not raise an exception
        data_ref[0,0] = 1
        mrc.close()
        assert not data_ref.flags.writeable
        with self.assertRaises(ValueError):
            data_ref[0,0] = 2


if __name__ == "__main__":
    unittest.main()
