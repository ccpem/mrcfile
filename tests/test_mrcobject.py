# coding: utf-8
# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for mrcobject.py
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io
import sys
import unittest
import warnings
from datetime import datetime

import numpy as np

from .helpers import AssertRaisesRegexMixin
from mrcfile import constants
from mrcfile.mrcobject import MrcObject
from mrcfile import utils


class MrcObjectTest(AssertRaisesRegexMixin, unittest.TestCase):
    
    """Unit tests for MrcObject class"""
    
    def setUp(self):
        super(MrcObjectTest, self).setUp()

        # Make sure we don't have any unexpected warnings by raising them all
        # as errors unless they are explicitly caught or ignored
        warning_context = warnings.catch_warnings()
        warning_context.__enter__()
        warnings.simplefilter("error")
        self.addCleanup(warning_context.__exit__)

        self.mrcobject = MrcObject()
        self.mrcobject._create_default_attributes()
    
    def test_attributes_are_empty_after_init(self):
        mrcobject = MrcObject()
        assert mrcobject.header is None
        assert mrcobject.extended_header is None
        assert mrcobject.data is None
    
    def test_check_writeable(self):
        assert not self.mrcobject._read_only
        self.mrcobject._check_writeable()  # should not throw
        self.mrcobject._read_only = True
        with self.assertRaisesRegex(ValueError, 'MRC object is read-only'):
            self.mrcobject._check_writeable()
    
    def test_calling_setters_raises_exception_if_read_only(self):
        
        self.mrcobject._read_only = True
        
        def assert_read_only(setter, *args):
            with self.assertRaisesRegex(ValueError, 'MRC object is read-only'):
                setter(*args)
        
        assert_read_only(self.mrcobject.set_extended_header, None)
        assert_read_only(self.mrcobject.set_data, None)
        assert_read_only(MrcObject.voxel_size.__set__, self.mrcobject, None)
        assert_read_only(self.mrcobject.set_image_stack)
        assert_read_only(self.mrcobject.set_volume)
        assert_read_only(self.mrcobject.update_header_from_data)
        assert_read_only(self.mrcobject.update_header_stats)
        assert_read_only(self.mrcobject.reset_header_stats)
    
    def test_default_header_is_correct(self):
        header = self.mrcobject.header
        assert header.map == b'MAP '
        assert header.nversion == 20141
        
        byte_order = '<' if sys.byteorder == 'little' else '>'
        expected_machst = utils._byte_order_to_machine_stamp[byte_order]
        assert np.array_equal(header.machst, expected_machst)
        
        assert header.nsymbt == 0
        assert header.ispg == constants.VOLUME_SPACEGROUP
        assert header.cellb.alpha == 90.0
        assert header.cellb.beta == 90.0
        assert header.cellb.gamma == 90.0
        assert header.mapc == 1
        assert header.mapr == 2
        assert header.maps == 3
    
    def test_default_extended_header_is_correct(self):
        ext = self.mrcobject.extended_header
        assert ext.size == 0
        assert ext.dtype == 'V1'
    
    def test_default_data_is_correct(self):
        data = self.mrcobject.data
        assert data.size == 0
        assert data.dtype == 'i1'
    
    def test_setting_header_attribute_raises_exception(self):
        with self.assertRaisesRegex(AttributeError,
                                    "can't set attribute|property .* has no setter"):
            self.mrcobject.header = np.zeros(1)
    
    def test_setting_extended_header_attribute_raises_exception(self):
        with self.assertRaisesRegex(AttributeError,
                                    "can't set attribute|property .* has no setter"):
            self.mrcobject.extended_header = np.zeros(1)
    
    def test_setting_data_attribute_raises_exception(self):
        with self.assertRaisesRegex(AttributeError,
                                    "can't set attribute|property .* has no setter"):
            self.mrcobject.data = np.zeros(1)
    
    def test_setting_extended_header(self):
        assert self.mrcobject.header.nsymbt == 0
        ext = np.empty((5, 10))
        self.mrcobject.set_extended_header(ext)
        assert self.mrcobject.extended_header is ext
        assert self.mrcobject.header.nsymbt == ext.nbytes
    
    def test_removing_extended_header(self):
        ext = np.empty((5, 10))
        self.mrcobject.set_extended_header(ext)
        assert self.mrcobject.extended_header.size > 0
        assert self.mrcobject.header.nsymbt > 0
        self.mrcobject.set_extended_header(np.empty(0))
        assert self.mrcobject.extended_header.size == 0
        assert self.mrcobject.header.nsymbt == 0
    
    def test_replacing_extended_header_different_size(self):
        ext = np.array('example extended header', dtype='S')
        self.mrcobject.set_extended_header(ext)
        assert self.mrcobject.extended_header is ext
        assert self.mrcobject.header.nsymbt == ext.nbytes
        ext2 = np.array('second example extended header', dtype='S')
        self.mrcobject.set_extended_header(ext2)
        assert self.mrcobject.extended_header is ext2
        assert self.mrcobject.header.nsymbt == ext2.nbytes
    
    def test_replacing_extended_header_same_size(self):
        ext = np.array('example extended header', dtype='S')
        self.mrcobject.set_extended_header(ext)
        assert self.mrcobject.extended_header is ext
        assert self.mrcobject.header.nsymbt == ext.nbytes
        ext2 = np.array('EXAMPLE EXTENDED HEADER', dtype='S')
        self.mrcobject.set_extended_header(ext2)
        assert self.mrcobject.extended_header is ext2
        assert self.mrcobject.header.nsymbt == ext2.nbytes
    
    def test_header_is_correct_for_2d_data(self):
        x, y = 3, 2
        data = np.arange(y * x, dtype=np.int16).reshape(y, x)
        self.mrcobject.set_data(data)
        assert self.mrcobject.is_single_image()
        header = self.mrcobject.header
        assert header.ispg == constants.IMAGE_STACK_SPACEGROUP
        assert header.nx == header.mx == x
        assert header.ny == header.my == y
        assert header.nz == header.mz == 1
    
    def test_switching_2d_data_to_image_stack_raises_exception(self):
        self.mrcobject.set_data(np.arange(6, dtype=np.int16).reshape(2, 3))
        with self.assertRaises(ValueError):
            self.mrcobject.set_image_stack()
    
    def test_switching_2d_data_to_volume_raises_exception(self):
        self.mrcobject.set_data(np.arange(6, dtype=np.int16).reshape(2, 3))
        with self.assertRaises(ValueError):
            self.mrcobject.set_volume()
    
    def test_header_is_correct_for_3d_data(self):
        x, y, z = 4, 3, 2
        self.mrcobject.set_data(np.arange(z * y * x, dtype=np.int16)
                                .reshape(z, y, x))
        assert self.mrcobject.is_volume()
        header = self.mrcobject.header
        assert header.ispg == constants.VOLUME_SPACEGROUP
        assert header.nx == header.mx == x
        assert header.ny == header.my == y
        assert header.nz == header.mz == z
    
    def test_switching_volume_to_image_stack(self):
        self.mrcobject.set_data(np.arange(12, dtype=np.int16).reshape(2, 2, 3))
        assert self.mrcobject.is_volume()
        self.mrcobject.set_image_stack()
        assert self.mrcobject.is_image_stack()
        assert self.mrcobject.header.ispg == constants.IMAGE_STACK_SPACEGROUP
        assert self.mrcobject.header.nz == 2
        assert self.mrcobject.header.mz == 1
    
    def test_can_call_set_volume_when_already_a_volume(self):
        self.mrcobject.set_data(np.arange(12, dtype=np.int16).reshape(2, 2, 3))
        assert self.mrcobject.is_volume()
        self.mrcobject.set_volume()
        assert self.mrcobject.is_volume()
    
    def test_switching_image_stack_to_volume(self):
        self.mrcobject.set_data(np.arange(12, dtype=np.int16).reshape(2, 2, 3))
        assert self.mrcobject.is_volume()
        self.mrcobject.set_image_stack()
        assert self.mrcobject.is_image_stack()
        self.mrcobject.set_volume()
        assert self.mrcobject.is_volume()
        assert self.mrcobject.header.ispg == constants.VOLUME_SPACEGROUP
        assert self.mrcobject.header.nz == self.mrcobject.header.mz == 2
    
    def test_can_call_set_image_stack_when_already_an_image_stack(self):
        self.mrcobject.set_data(np.arange(12, dtype=np.int16).reshape(2, 2, 3))
        self.mrcobject.set_image_stack()
        assert self.mrcobject.is_image_stack()
        self.mrcobject.set_image_stack()
        assert self.mrcobject.is_image_stack()
    
    def test_image_stack_with_new_3d_data_is_still_image_stack(self):
        self.mrcobject.set_data(np.arange(12, dtype=np.int16).reshape(2, 2, 3))
        self.mrcobject.set_image_stack()
        assert self.mrcobject.is_image_stack()
        self.mrcobject.set_data(np.arange(24, dtype=np.int16).reshape(2, 3, 4))
        assert self.mrcobject.is_image_stack()
    
    def test_header_is_correct_for_4d_data(self):
        x, y, z, nvol = 3, 4, 5, 6
        vstack = (np.arange(nvol * z * y * x, dtype=np.int16)
                  .reshape(nvol, z, y, x))
        self.mrcobject.set_data(vstack)
        assert self.mrcobject.is_volume_stack()
        header = self.mrcobject.header
        assert header.ispg == constants.VOLUME_STACK_SPACEGROUP
        assert header.nx == header.mx == x
        assert header.ny == header.my == y
        assert header.nz == z * nvol
        assert header.mz == z
    
    def test_volume_stack_spacegroup_is_preserved_for_4d_data(self):
        x, y, z, nvol = 3, 4, 5, 6
        vstack = (np.arange(nvol * z * y * x, dtype=np.int16)
                  .reshape(nvol, z, y, x))
        self.mrcobject.set_data(vstack)
        spacegroup = 602
        self.mrcobject.header.ispg = spacegroup
        assert self.mrcobject.is_volume_stack()
        
        self.mrcobject.set_data(vstack.copy().reshape(x, z, y, nvol))
        assert self.mrcobject.is_volume_stack()
        assert self.mrcobject.header.ispg == spacegroup
    
    def test_switching_4d_data_to_image_stack_raises_exception(self):
        self.mrcobject.set_data(np.arange(24, dtype=np.int16)
                                .reshape(2, 2, 2, 3))
        with self.assertRaises(ValueError):
            self.mrcobject.set_image_stack()
    
    def test_switching_4d_data_to_volume_raises_exception(self):
        self.mrcobject.set_data(np.arange(24, dtype=np.int16)
                                .reshape(2, 2, 2, 3))
        with self.assertRaises(ValueError):
            self.mrcobject.set_volume()
    
    def test_1d_data_raises_exception(self):
        with self.assertRaises(ValueError):
            self.mrcobject.set_data(np.arange(2, dtype=np.int16))
    
    def test_5d_data_raises_exception(self):
        with self.assertRaises(ValueError):
            self.mrcobject.set_data(np.arange(2, dtype=np.int16)
                                    .reshape(1, 1, 1, 1, 2))
    
    def assert_dtype_raises_exception(self, data):
        with self.assertRaisesRegex(ValueError, 'dtype'):
            self.mrcobject.set_data(data)
    
    def test_complex256_dtype_raises_exception(self):
        # complex256 only exists on some platforms
        if hasattr(np, 'complex256'):
            data = np.arange(6, dtype=np.complex256).reshape(3, 2)
            self.assert_dtype_raises_exception(data)
    
    def test_complex128_dtype_raises_exception(self):
        data = np.arange(6, dtype=np.complex128).reshape(3, 2)
        self.assert_dtype_raises_exception(data)
    
    def test_float64_dtype_raises_exception(self):
        data = np.arange(6, dtype=np.float64).reshape(3, 2)
        self.assert_dtype_raises_exception(data)
    
    def test_int32_dtype_raises_exception(self):
        data = np.arange(6, dtype=np.int32).reshape(3, 2)
        self.assert_dtype_raises_exception(data)
    
    def test_int8_dtype_is_preserved_in_mode_0(self):
        data = np.arange(6, dtype=np.int8).reshape(3, 2)
        self.mrcobject.set_data(data)
        assert self.mrcobject.data.dtype == np.int8
        assert self.mrcobject.header.mode == 0
    
    def test_int16_dtype_is_preserved_in_mode_1(self):
        data = np.arange(6, dtype=np.int16).reshape(3, 2)
        self.mrcobject.set_data(data)
        assert self.mrcobject.data.dtype == np.int16
        assert self.mrcobject.header.mode == 1
    
    def test_float32_dtype_is_preserved_in_mode_2(self):
        data = np.arange(6, dtype=np.float32).reshape(3, 2)
        self.mrcobject.set_data(data)
        assert self.mrcobject.data.dtype == np.float32
        assert self.mrcobject.header.mode == 2
    
    def test_complex64_dtype_is_preserved_in_mode_4(self):
        data = np.arange(6, dtype=np.complex64).reshape(3, 2)
        # Suppress complex casting warnings from statistics calculations
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", np.ComplexWarning)
            self.mrcobject.set_data(data)
            assert self.mrcobject.data.dtype == np.complex64
            assert self.mrcobject.header.mode == 4
    
    def test_uint16_dtype_is_preserved_in_mode_6(self):
        data = np.arange(6, dtype=np.uint16).reshape(3, 2)
        self.mrcobject.set_data(data)
        assert self.mrcobject.data.dtype == np.uint16
        assert self.mrcobject.header.mode == 6
    
    def test_float16_dtype_is_preserved_in_mode_12(self):
        data = np.arange(6, dtype=np.float16).reshape(3, 2)
        self.mrcobject.set_data(data)
        assert self.mrcobject.data.dtype == np.float16
        assert self.mrcobject.header.mode == 12
    
    def test_uint8_dtype_is_widened_in_mode_6(self):
        data = np.arange(6, dtype=np.uint8).reshape(3, 2)
        self.mrcobject.set_data(data)
        assert self.mrcobject.data.dtype == np.uint16
        assert self.mrcobject.header.mode == 6
    
    def test_data_is_not_copied_unnecessarily(self):
        data = np.arange(6, dtype=np.int16).reshape(1, 2, 3)
        self.mrcobject.set_data(data)
        assert self.mrcobject.data is data
    
    def test_header_byte_order_is_unchanged_by_data_with_native_order(self):
        data = np.arange(6, dtype=np.float32).reshape(3, 2)
        header = self.mrcobject.header
        original_mapc = int(header.mapc)
        assert utils.byte_orders_equal(header.mode.dtype.byteorder,
                                       data.dtype.byteorder)
        self.mrcobject.set_data(data)
        assert utils.byte_orders_equal(header.mode.dtype.byteorder,
                                       data.dtype.byteorder)
        assert header.mode == 2
        assert header.mapc == original_mapc
    
    def test_header_byte_order_is_unchanged_by_data_with_no_order(self):
        data = np.arange(6, dtype=np.int8).reshape(3, 2)
        header = self.mrcobject.header
        original_mapc = int(header.mapc)
        original_order = header.mode.dtype.byteorder
        self.mrcobject.set_data(data)
        assert header.mode.dtype.byteorder == original_order
        assert header.mode == 0
        assert header.mapc == original_mapc
    
    def test_header_byte_order_is_changed_by_data_with_opposite_order(self):
        data = np.arange(6, dtype=np.float32).reshape(3, 2)
        orig_byte_order = data.dtype.byteorder
        header = self.mrcobject.header
        original_mapc = int(header.mapc)
        assert utils.byte_orders_equal(header.mode.dtype.byteorder,
                                       orig_byte_order)
        
        self.mrcobject.set_data(data.newbyteorder())
        assert not utils.byte_orders_equal(header.mode.dtype.byteorder,
                                           orig_byte_order)
        assert header.mode == 2
        assert header.mapc == original_mapc
        
        self.mrcobject.set_data(data)
        assert utils.byte_orders_equal(header.mode.dtype.byteorder,
                                       orig_byte_order)
        assert header.mode == 2
        assert header.mapc == original_mapc
    
    def test_non_c_contiguous_data_is_made_c_contiguous(self):
        x, y, z = 4, 3, 2
        data = np.arange(z * y * x, dtype=np.int16).reshape(z, y, x).transpose()
        assert data.flags.c_contiguous == False
        self.mrcobject.set_data(data)
        assert self.mrcobject.data.flags.c_contiguous == True
        assert self.mrcobject.data is not data
    
    def test_new_header_stats_are_undetermined(self):
        header = self.mrcobject.header
        assert header.dmax < header.dmin
        assert header.dmean < header.dmin
        assert header.dmean < header.dmax
        assert header.rms < 0
    
    def test_stats_are_updated_for_new_data(self):
        x, y, z = 10, 9, 5
        img = np.linspace(-32768, 32767, x * y, dtype=np.int16).reshape(y, x)
        vol = img // np.arange(1, 6, dtype=np.int16).reshape(z, 1, 1)
        
        self.mrcobject.set_data(vol)
        header = self.mrcobject.header
        assert header.dmin == np.float32(vol.min())
        assert header.dmax == np.float32(vol.max())
        assert header.dmean == np.float32(vol.mean(dtype=np.float32))
        assert header.rms == np.float32(vol.std(dtype=np.float32))
    
    def test_stats_are_updated_on_request(self):
        x, y = 4, 3
        zeros = np.zeros(x * y, dtype=np.int16).reshape(y, x)
        data = np.arange(x * y, dtype=np.int16).reshape(y, x)
        
        # Set data with zeros
        self.mrcobject.set_data(zeros)
        
        # Now replace with non-zero data, in place
        self.mrcobject.data[:] = data[:]
        
        # Header values should have been set from the original zeros
        header = self.mrcobject.header
        assert header.dmin == 0.0
        assert header.dmax == 0.0
        assert header.dmean == 0.0
        assert header.rms == 0.0
        
        # Now explicitly update the stats
        self.mrcobject.update_header_stats()
        assert header.dmin == np.float32(data.min())
        assert header.dmax == np.float32(data.max())
        assert header.dmean == np.float32(data.mean(dtype=np.float64))
        assert header.rms == np.float32(data.std())

    def test_reset_header_stats_are_undetermined(self):
        self.mrcobject.set_data(np.arange(12, dtype=np.float32).reshape(3, 4))
        header = self.mrcobject.header
        assert header.dmax > header.dmin
        assert header.dmean > header.dmin
        assert header.dmean < header.dmax
        assert header.rms > 0
        self.mrcobject.reset_header_stats()
        assert header.dmax < header.dmin
        assert header.dmean < header.dmin
        assert header.dmean < header.dmax
        assert header.rms < 0
    
    def test_header_stats_are_undetermined_after_setting_empty_data(self):
        self.mrcobject.set_data(np.array((), dtype=np.float32).reshape((0, 0, 0)))
        header = self.mrcobject.header
        assert header.dmax < header.dmin
        assert header.dmean < header.dmin
        assert header.dmean < header.dmax
        assert header.rms < 0

    def test_header_stats_are_undetermined_after_setting_empty_complex_data(self):
        self.mrcobject.set_data(np.array((), dtype=np.complex64).reshape((0, 0, 0)))
        header = self.mrcobject.header
        assert header.dmax < header.dmin
        assert header.dmean < header.dmin
        assert header.dmean < header.dmax
        assert header.rms < 0

    def test_header_stats_setting_complex_data(self):
        data = np.arange(6, dtype=np.complex64).reshape(3, 2)
        with warnings.catch_warnings(record=True) as w:
            # Hack for warnings bug in Python 2.7
            #  See https://stackoverflow.com/q/56821539
            if sys.version_info[0:2] == (2, 7):
                from mrcfile import mrcobject
                if hasattr(mrcobject, '__warningregistry__'):
                    mrcobject.__warningregistry__.clear()
            warnings.simplefilter("always")
            self.mrcobject.set_data(data)
            assert len(w) == 0
            header = self.mrcobject.header
            assert header.dmax < header.dmin
            assert header.dmean < header.dmin
            assert header.dmean < header.dmax
            self.assertAlmostEqual(header.rms, np.float32(data.std()))

    def test_warning_for_stats_with_nan(self):
        data = np.arange(6, dtype=np.float32).reshape(3, 2)
        data[1,1] = np.nan
        with warnings.catch_warnings(record=True) as w:
            # Hack for warnings bug in Python 2.7
            #  See https://stackoverflow.com/q/56821539
            if sys.version_info[0:2] == (2, 7):
                from mrcfile import mrcobject
                if hasattr(mrcobject, '__warningregistry__'):
                    mrcobject.__warningregistry__.clear()
            warnings.simplefilter("always")
            self.mrcobject.set_data(data)
            assert len(w) >= 1, str(len(w)) + " warnings issued"
            assert "Data array contains NaN values" in [str(i.message) for i in w]
            header = self.mrcobject.header
            assert np.isnan(header.dmin)
            assert np.isnan(header.dmax)
            assert np.isnan(header.dmean)
            assert np.isnan(header.rms)

    def test_warning_for_stats_with_inf(self):
        data = np.arange(6, dtype=np.float32).reshape(3, 2)
        data[0,1] = np.inf
        data[1,1] = -np.inf
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.mrcobject.set_data(data)
            assert len(w) >= 1, str(len(w)) + " warnings issued"
            assert "Data array contains infinite values" in [str(i.message) for i in w]
            header = self.mrcobject.header
            assert header.dmin == np.NINF
            assert header.dmax == np.inf
            assert np.isnan(header.dmean)
            assert np.isnan(header.rms)

    def test_getting_voxel_size(self):
        # Need to set some data first to avoid zero division error
        x, y, z = 4, 3, 1
        data = np.arange(x * y, dtype=np.int16).reshape(z, y, x)
        self.mrcobject.set_data(data)
        voxel_size = self.mrcobject.voxel_size
        assert voxel_size.x == 0.0
        assert voxel_size.y == 0.0
        assert voxel_size.z == 0.0
        assert not voxel_size.flags.writeable
        with self.assertRaisesRegex(ValueError, "read-only"):
            voxel_size.x = 1.1
    
    def test_setting_voxel_size_as_single_number(self):
        x, y, z = 4, 3, 1
        data = np.arange(x * y, dtype=np.int16).reshape(z, y, x)
        
        mrcobj = self.mrcobject
        mrcobj.set_data(data)
        assert mrcobj.voxel_size.x == 0.0
        assert mrcobj.voxel_size.y == 0.0
        assert mrcobj.voxel_size.z == 0.0
        
        voxel_size = 1.530
        mrcobj.voxel_size = voxel_size
        self.assertAlmostEqual(mrcobj.voxel_size.x, voxel_size, places=3)
        self.assertAlmostEqual(mrcobj.voxel_size.y, voxel_size, places=3)
        self.assertAlmostEqual(mrcobj.voxel_size.z, voxel_size, places=3)
    
    def test_setting_voxel_size_as_tuple(self):
        x, y, z = 4, 3, 1
        data = np.arange(x * y, dtype=np.int16).reshape(z, y, x)
        
        mrcobj = self.mrcobject
        mrcobj.set_data(data)
        assert mrcobj.voxel_size.x == 0.0
        assert mrcobj.voxel_size.y == 0.0
        assert mrcobj.voxel_size.z == 0.0
        
        voxel_size = (1.1, 2.2, 3.3)
        mrcobj.voxel_size = voxel_size
        
        # Check the new (re-calculated) values
        self.assertAlmostEqual(mrcobj.voxel_size.x, voxel_size[0], places=3)
        self.assertAlmostEqual(mrcobj.voxel_size.y, voxel_size[1], places=3)
        self.assertAlmostEqual(mrcobj.voxel_size.z, voxel_size[2], places=3)
        
        # Also check the header values
        assert mrcobj.header.mx == 4
        assert mrcobj.header.my == 3
        assert mrcobj.header.mz == 1
        self.assertAlmostEqual(mrcobj.header.cella.x, 4.4, places=3)
        self.assertAlmostEqual(mrcobj.header.cella.y, 6.6, places=3)
        self.assertAlmostEqual(mrcobj.header.cella.z, 3.3, places=3)
    
    def test_setting_voxel_size_as_modified_array(self):
        x, y, z = 4, 3, 1
        data = np.arange(x * y, dtype=np.int16).reshape(z, y, x)
        
        mrcobject = self.mrcobject
        mrcobject.set_data(data)
        assert mrcobject.voxel_size.x == 0.0
        assert mrcobject.voxel_size.y == 0.0
        assert mrcobject.voxel_size.z == 0.0
        
        voxel_size = mrcobject.voxel_size

        with self.assertRaisesRegex(ValueError, "read-only"):
            voxel_size.x = 1.1

        voxel_size.flags.writeable = True
        voxel_size.x = 1.1
        voxel_size.y = 2.2
        voxel_size.z = 3.3
        mrcobject.voxel_size = voxel_size
        self.assertAlmostEqual(mrcobject.voxel_size.x, 1.1, places=3)
        self.assertAlmostEqual(mrcobject.voxel_size.y, 2.2, places=3)
        self.assertAlmostEqual(mrcobject.voxel_size.z, 3.3, places=3)

    def test_getting_nstart(self):
        nstart = self.mrcobject.nstart
        assert nstart.x == 0
        assert nstart.y == 0
        assert nstart.z == 0
        assert not nstart.flags.writeable
        with self.assertRaisesRegex(ValueError, "read-only"):
            nstart.x = 1

    def test_setting_nstart_as_tuple(self):
        x, y, z = 20, 20, 20
        data = np.arange(x * y * z, dtype=np.int16).reshape(z, y, x)

        mrcobj = self.mrcobject
        mrcobj.set_data(data)
        assert mrcobj.header.nxstart == 0
        assert mrcobj.header.nystart == 0
        assert mrcobj.header.nzstart == 0

        offsets = (-1, -5, -10)
        mrcobj.nstart = offsets
        assert mrcobj.header.nxstart == offsets[0]
        assert mrcobj.header.nystart == offsets[1]
        assert mrcobj.header.nzstart == offsets[2]

    def test_setting_nstart_as_single_number(self):
        x, y, z = 20, 20, 20
        data = np.arange(x * y * z, dtype=np.int16).reshape(z, y, x)

        mrcobj = self.mrcobject
        mrcobj.set_data(data)
        assert mrcobj.header.nxstart == 0
        assert mrcobj.header.nystart == 0
        assert mrcobj.header.nzstart == 0

        offset = -10
        mrcobj.nstart = offset
        assert mrcobj.header.nxstart == offset
        assert mrcobj.header.nystart == offset
        assert mrcobj.header.nzstart == offset

    def test_setting_nstart_as_modified_array(self):
        x, y, z = 20, 20, 20
        data = np.arange(x * y * z, dtype=np.int16).reshape(z, y, x)

        mrcobj = self.mrcobject
        mrcobj.set_data(data)
        assert mrcobj.header.nxstart == 0
        assert mrcobj.header.nystart == 0
        assert mrcobj.header.nzstart == 0

        offsets = mrcobj.nstart
        offsets.flags.writeable = True
        offsets.x = 4
        offsets.y = 100
        offsets.z = -5
        mrcobj.nstart = offsets
        assert mrcobj.header.nxstart == 4
        assert mrcobj.header.nystart == 100
        assert mrcobj.header.nzstart == -5
    
    def test_new_header_contains_creator_label(self):
        assert self.mrcobject.header.nlabl == 1
        label = self.mrcobject.header.label[0].decode()
        assert label.startswith('Created by mrcfile.py    ')
        time = label[-40:].strip()
        datetime.strptime(time, '%Y-%m-%d %H:%M:%S')  # will throw if bad format

    def test_get_labels(self):
        labels = self.mrcobject.get_labels()
        assert len(labels) == 1
        assert labels[0].startswith('Created by mrcfile.py    ')

    def test_get_labels_strips_unprintable_characters(self):
        self.mrcobject.header.label[0] = b'Test \nlabel\x01\x00'
        labels = self.mrcobject.get_labels()
        assert labels[0] == 'Test label'

    def test_add_label_with_normal_string(self):
        self.mrcobject.add_label('Test label')
        assert self.mrcobject.header.nlabl == 2
        labels = self.mrcobject.get_labels()
        assert len(labels) == 2
        assert labels[0].startswith('Created by mrcfile.py    ')
        assert labels[1] == 'Test label'

    def test_adding_too_long_label_raises_exception(self):
        with self.assertRaises(ValueError):
            self.mrcobject.add_label('-' * 81)

    def test_adding_more_than_ten_labels_raises_exception(self):
        self.mrcobject.header.nlabl = 10
        with self.assertRaises(IndexError):
            self.mrcobject.add_label('Test label')

    def test_adding_non_ascii_label_raises_exception(self):
        with self.assertRaisesRegex(ValueError, "non-printable or non-ASCII"):
            self.mrcobject.add_label('Test label £')

    def test_adding_non_printable_label_raises_exception(self):
        with self.assertRaisesRegex(ValueError, "non-printable or non-ASCII"):
            self.mrcobject.add_label('Test label \n\x00')
    
    def test_print_header(self):
        print_stream = io.StringIO()
        self.mrcobject.print_header(print_stream)
        output = print_stream.getvalue()
        print_stream.close()
        out_lines = output.split('\n')
        # Number of lines is different in python 2 and 3 due to different numpy
        # output formatting - just check for both possibilities for now
        assert len(out_lines) == 32 or len(out_lines) == 34
    
    def test_validate(self):
        self.mrcobject.header.ispg = -10
        print_stream = io.StringIO()
        result = self.mrcobject.validate(print_file=print_stream)
        assert result == False
        print_output = print_stream.getvalue()
        assert "Header field 'ispg' is negative" in print_output


if __name__ == '__main__':
    unittest.main()
