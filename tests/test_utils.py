# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for utils.py
"""

# Import Python 3 features for future-proofing
# Deliberately do NOT import unicode_literals due to a bug in numpy dtypes:
# https://github.com/numpy/numpy/issues/2407
from __future__ import absolute_import, division, print_function

import sys
import unittest

import numpy as np

import mrcfile.utils as utils
from .helpers import AssertRaisesRegexMixin
from mrcfile.dtypes import HEADER_DTYPE


class UtilsTest(AssertRaisesRegexMixin, unittest.TestCase):
    
    """Unit tests for mrcfile.utils"""
    
    def test_header_dtype_is_correct_length(self):
        assert HEADER_DTYPE.itemsize == 1024
    
    def test_mode_0_is_converted_to_int8(self):
        dtype = utils.dtype_from_mode(0)
        assert dtype == np.dtype(np.int8)
    
    def test_mode_1_is_converted_to_int16(self):
        dtype = utils.dtype_from_mode(1)
        assert dtype == np.dtype(np.int16)
    
    def test_mode_2_is_converted_to_float32(self):
        dtype = utils.dtype_from_mode(2)
        assert dtype == np.dtype(np.float32)
    
    def test_mode_3_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.dtype_from_mode(3)
    
    def test_mode_4_is_converted_to_complex64(self):
        dtype = utils.dtype_from_mode(4)
        assert dtype == np.dtype(np.complex64)
    
    def test_mode_6_is_converted_to_uint16(self):
        dtype = utils.dtype_from_mode(6)
        assert dtype == np.dtype(np.uint16)
    
    def test_undefined_modes_raise_exception(self):
        for mode in (x for x in range(-33, 34, 1) if x not in [0, 1, 2, 4, 6]):
            with self.assertRaises(ValueError):
                utils.dtype_from_mode(mode)
    
    def test_mode_scalar_is_converted_without_error(self):
        dtype = utils.dtype_from_mode(np.float32(1))
        assert dtype == np.dtype(np.int16)
    
    def test_mode_zerodim_array_is_converted_without_error(self):
        dtype = utils.dtype_from_mode(np.array(1))
        assert dtype == np.dtype(np.int16)
    
    def test_mode_onedim_array_is_converted_without_error(self):
        dtype = utils.dtype_from_mode(np.array([1]))
        assert dtype == np.dtype(np.int16)
    
    def test_float16_dtype_is_converted_to_mode_2(self):
        mode = utils.mode_from_dtype(np.dtype(np.float16))
        assert mode == 2
    
    def test_float32_dtype_is_converted_to_mode_2(self):
        mode = utils.mode_from_dtype(np.dtype(np.float32))
        assert mode == 2
    
    def test_float64_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype(np.float64))
    
    def test_float128_dtype_raises_exception(self):
        # float128 only exists on some platforms
        if hasattr(np, 'float128'):
            with self.assertRaises(ValueError):
                utils.mode_from_dtype(np.dtype(np.float128))
    
    def test_int8_dtype_is_converted_to_mode_0(self):
        mode = utils.mode_from_dtype(np.dtype(np.int8))
        assert mode == 0
    
    def test_int16_dtype_is_converted_to_mode_1(self):
        mode = utils.mode_from_dtype(np.dtype(np.int16))
        assert mode == 1
    
    def test_int32_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype(np.int32))
    
    def test_int64_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype(np.int64))
    
    def test_uint8_dtype_is_converted_to_mode_6(self):
        mode = utils.mode_from_dtype(np.dtype(np.uint8))
        assert mode == 6
    
    def test_uint16_dtype_is_converted_to_mode_6(self):
        mode = utils.mode_from_dtype(np.dtype(np.uint16))
        assert mode == 6
    
    def test_uint32_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype(np.uint32))
    
    def test_uint64_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype(np.uint64))
    
    def test_complex64_dtype_is_converted_to_mode_4(self):
        mode = utils.mode_from_dtype(np.dtype(np.complex64))
        assert mode == 4
    
    def test_complex128_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype(np.complex128))
    
    def test_string_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype('S1'))
    
    def test_unicode_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype('U1'))
    
    def test_bool_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype(np.bool))
    
    def test_object_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype(object))
    
    def test_structured_dtype_raises_exception(self):
        with self.assertRaises(ValueError):
            utils.mode_from_dtype(np.dtype([('f1', np.int32)]))
    
    def test_little_endian_machine_stamp(self):
        machst = utils.machine_stamp_from_byte_order('<')
        assert machst == bytearray((0x44, 0x44, 0x00, 0x00))
    
    def test_big_endian_machine_stamp(self):
        machst = utils.machine_stamp_from_byte_order('>')
        assert machst == bytearray((0x11, 0x11, 0x00, 0x00))
    
    def test_native_machine_stamp(self):
        machst = utils.machine_stamp_from_byte_order()
        if sys.byteorder == 'little':
            assert machst == utils.machine_stamp_from_byte_order('<')
        else:
            assert machst == utils.machine_stamp_from_byte_order('>')
    
    def test_normalise_little_endian_byte_order(self):
        assert utils.normalise_byte_order('<') == '<'
    
    def test_normalise_big_endian_byte_order(self):
        assert utils.normalise_byte_order('>') == '>'
    
    def test_normalise_native_byte_order(self):
        if sys.byteorder == 'little':
            assert utils.normalise_byte_order('=') == '<'
        else:
            assert utils.normalise_byte_order('=') == '>'
    
    def test_normalise_unknown_byte_orders(self):
        for byte_order in ['|', 'I', 'other', 'S', 'N', 'L', 'B']:
            with self.assertRaisesRegex(ValueError,
                                        "Unrecognised byte order indicator"):
                utils.normalise_byte_order(byte_order)
    
    def test_native_byte_orders_equal(self):
        assert utils.byte_orders_equal('=', '=')
    
    def test_little_byte_order_equals_native(self):
        assert utils.byte_orders_equal('<', '=') == (sys.byteorder == 'little')
    
    def test_big_byte_order_equals_native(self):
        assert utils.byte_orders_equal('>', '=') == (sys.byteorder == 'big')
    
    def test_little_byte_orders_equal(self):
        assert utils.byte_orders_equal('<', '<')
    
    def test_big_byte_orders_equal(self):
        assert utils.byte_orders_equal('>', '>')
    
    def test_unequal_byte_orders(self):
        assert not utils.byte_orders_equal('>', '<')
    
    def test_equality_of_invalid_byte_orders(self):
        for pair in [('|', '<'),
                     ('|', '>'),
                     ('|', '='),
                     ('<', '|'),
                     ('>', '|'),
                     ('=', '|'),
                     ('|', '|')]:
            with self.assertRaisesRegex(ValueError,
                                        "Unrecognised byte order indicator"):
                utils.byte_orders_equal(*pair)
    
    def test_unknown_byte_order_raises_exception(self):
        with self.assertRaisesRegex(ValueError, "Unrecognised byte order indicator"):
            utils.machine_stamp_from_byte_order('|')
    
    def test_spacegroup_is_volume_stack(self):
        for ispg in range(-2000, 2000):
            assert utils.spacegroup_is_volume_stack(ispg) == (401 <= ispg <= 630)

    def test_pretty_machine_stamp(self):
        machst = utils.machine_stamp_from_byte_order('<')
        assert utils.pretty_machine_stamp(machst) == "0x44 0x44 0x00 0x00"


if __name__ == '__main__':
    unittest.main()
