# Copyright (c) 2022, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for dtypes.py
"""

# Import Python 3 features for future-proofing
# Deliberately do NOT import unicode_literals due to a bug in numpy dtypes:
# https://github.com/numpy/numpy/issues/2407
from __future__ import absolute_import, division, print_function

import unittest

import mrcfile.dtypes as dtypes
import mrcfile.utils as utils
from .helpers import AssertRaisesRegexMixin


class DtypesTest(AssertRaisesRegexMixin, unittest.TestCase):
    
    """Unit tests for mrcfile.dtypes"""

    def test_invalid_byte_order_raises_exception(self):
        with self.assertRaisesRegex(ValueError, "Unrecognised byte order indicator"):
            _ = dtypes.get_ext_header_dtype('', 'a')
    
    def test_fei1_ext_header_with_native_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b'FEI1')
        assert dtype.itemsize == 768
        assert utils.byte_orders_equal(dtype['Metadata size'].byteorder, '=')
        with self.assertRaises(KeyError):
            _ = dtype['Scan rotation']
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype['Bitmask 1'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 2'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 3'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 4'].byteorder, '<')

    def test_fei2_ext_header_with_native_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b'FEI2')
        assert dtype.itemsize == 888
        assert utils.byte_orders_equal(dtype['Metadata size'].byteorder, '=')
        assert dtype['Scan rotation'] is not None
        assert utils.byte_orders_equal(dtype['Scan rotation'].byteorder, '=')
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype['Bitmask 1'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 2'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 3'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 4'].byteorder, '<')

    def test_fei1_ext_header_with_little_endian_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b'FEI1', '<')
        # Normal fields should match the requested byte order
        assert utils.byte_orders_equal(dtype['Metadata size'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Alpha tilt'].byteorder, '<')
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype['Bitmask 1'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 2'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 3'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 4'].byteorder, '<')

    def test_fei2_ext_header_with_little_endian_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b'FEI2', '<')
        # Normal fields should match the requested byte order
        assert utils.byte_orders_equal(dtype['Metadata size'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Alpha tilt'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Scan rotation'].byteorder, '<')
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype['Bitmask 1'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 2'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 3'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 4'].byteorder, '<')

    def test_fei1_ext_header_with_big_endian_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b'FEI1', '>')
        # Normal fields should match the requested byte order
        assert utils.byte_orders_equal(dtype['Metadata size'].byteorder, '>')
        assert utils.byte_orders_equal(dtype['Alpha tilt'].byteorder, '>')
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype['Bitmask 1'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 2'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 3'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 4'].byteorder, '<')

    def test_fei2_ext_header_with_big_endian_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b'FEI2', '>')
        # Normal fields should match the requested byte order
        assert utils.byte_orders_equal(dtype['Metadata size'].byteorder, '>')
        assert utils.byte_orders_equal(dtype['Alpha tilt'].byteorder, '>')
        assert utils.byte_orders_equal(dtype['Scan rotation'].byteorder, '>')
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype['Bitmask 1'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 2'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 3'].byteorder, '<')
        assert utils.byte_orders_equal(dtype['Bitmask 4'].byteorder, '<')


if __name__ == '__main__':
    unittest.main()
