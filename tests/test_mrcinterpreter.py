# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for mrcinterpreter.py
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io
import unittest

from .test_mrcobject import MrcObjectTest
from mrcfile.constants import MAP_ID_OFFSET_BYTES
from mrcfile.mrcinterpreter import MrcInterpreter


class MrcInterpreterTest(MrcObjectTest):
    
    """Unit tests for MrcInterpreter class.
    
    Note that this test class inherits MrcObjectTest to ensure all of the tests
    for MrcObject work correctly for the MrcInterpreter subclass.
    
    """
    
    def setUp(self):
        super(MrcInterpreterTest, self).setUp()
        
        # Set up parameters so MrcObject tests run on the MrcInterpreter class
        self.mrcobject = MrcInterpreter()
        self.mrcobject._create_default_attributes()
    
    def test_incorrect_map_id(self):
        stream = io.BytesIO()
        stream.write(bytearray(1024))
        stream.seek(MAP_ID_OFFSET_BYTES)
        stream.write(b'map ')
        stream.seek(0)
        mrcinterpreter = MrcInterpreter(iostream=stream)
        with self.assertRaisesRegex(ValueError, "Map ID string not found"):
            mrcinterpreter._read_stream()
    
    def test_incorrect_machine_stamp(self):
        stream = io.BytesIO()
        stream.write(bytearray(1024))
        stream.seek(MAP_ID_OFFSET_BYTES)
        stream.write(b'MAP ')
        stream.seek(0)
        mrcinterpreter = MrcInterpreter(iostream=stream)
        with self.assertRaisesRegex(ValueError, "Unrecognised machine stamp: "
                                                 "0x00 0x00 0x00 0x00"):
            mrcinterpreter._read_stream()


if __name__ == '__main__':
    unittest.main()
