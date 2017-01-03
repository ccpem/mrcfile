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

from mrcfile.mrcmemmap import MrcMemmap
from tests.test_mrcfile import MrcFileTest


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


if __name__ == "__main__":
    unittest.main()
