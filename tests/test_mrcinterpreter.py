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
import warnings

import numpy as np

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
        with self.assertRaisesRegex(ValueError, "Map ID string not found"):
            MrcInterpreter(iostream=stream)
    
    def test_incorrect_machine_stamp(self):
        stream = io.BytesIO()
        stream.write(bytearray(1024))
        stream.seek(MAP_ID_OFFSET_BYTES)
        stream.write(b'MAP ')
        stream.seek(0)
        with self.assertRaisesRegex(ValueError, "Unrecognised machine stamp: "
                                                "0x00 0x00 0x00 0x00"):
            MrcInterpreter(iostream=stream)
    
    def test_stream_too_short(self):
        stream = io.BytesIO()
        stream.write(bytearray(1023))
        with self.assertRaisesRegex(ValueError, "Couldn't read enough bytes for MRC header"):
            MrcInterpreter(iostream=stream)
    
    def test_stream_writing_and_reading(self):
        stream = io.BytesIO()
        data = np.arange(30, dtype=np.int16).reshape(5, 6)
        with MrcInterpreter() as mrc:
            mrc._iostream = stream
            mrc._create_default_attributes()
            mrc.set_data(data)
        stream.seek(0)
        with MrcInterpreter(iostream=stream) as mrc:
            np.testing.assert_array_equal(data, mrc.data)
            assert mrc.header.mode == 1
            mrc.set_data(data * 2)
            assert mrc.header.mode == 1
    
    def test_permissive_read_mode_with_wrong_map_id_and_machine_stamp(self):
        stream = io.BytesIO()
        stream.write(bytearray(1024))
        stream.seek(MAP_ID_OFFSET_BYTES)
        stream.write(b'map ')
        stream.seek(0)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            MrcInterpreter(iostream=stream, permissive=True)
            
            assert len(w) == 2
            assert "Map ID string not found" in str(w[0].message)
            assert "Unrecognised machine stamp" in str(w[1].message)
    
    def test_permissive_read_mode_with_file_too_small_for_extended_header(self):
        stream = io.BytesIO()
        mrc = MrcInterpreter()
        mrc._iostream = stream
        mrc._create_default_attributes()
        mrc.set_extended_header(np.arange(12, dtype=np.int16).reshape(1, 3, 4))
        mrc.close()
        stream.seek(-1, io.SEEK_CUR)
        stream.truncate()
        stream.seek(0)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            MrcInterpreter(iostream=stream, permissive=True)
            
            assert len(w) == 1
            assert ("Expected 24 bytes in extended header but could only read 23"
                    in str(w[0].message))

    def test_permissive_read_mode_with_file_too_small_for_data(self):
        stream = io.BytesIO()
        mrc = MrcInterpreter()
        mrc._iostream = stream
        mrc._create_default_attributes()
        mrc.set_data(np.arange(12, dtype=np.int16).reshape(1, 3, 4))
        mrc.close()
        stream.seek(-1, io.SEEK_CUR)
        stream.truncate()
        stream.seek(0)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            MrcInterpreter(iostream=stream, permissive=True)

            assert len(w) == 1
            assert ("Expected 24 bytes in data block but could only read 23"
                    in str(w[0].message))


if __name__ == '__main__':
    unittest.main()
