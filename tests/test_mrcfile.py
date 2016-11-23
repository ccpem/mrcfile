# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for mrcfile.py
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import shutil
import sys
import tempfile
import unittest
import warnings
from datetime import datetime

import numpy as np

import mrcfile
import mrcfile.utils as utils
from mrcfile import MrcFile
from tests import test_data


class MrcFileTest(unittest.TestCase):
    
    """Unit tests for MRC file I/O."""
    
    def setUp(self):
        self.test_data = test_data.get_test_data_path()
        self.test_output = tempfile.mkdtemp()
        self.temp_mrc_name = os.path.join(self.test_output, 'test_file.mrc')
        self.example_mrc_name = os.path.join(self.test_data, 'EMD-3197.map')
    
    def tearDown(self):
        if os.path.exists(self.test_output):
            shutil.rmtree(self.test_output)
    
    ############################################################################
    #
    # Tests which depend on existing files (in the test_data directory)
    #
    
    def test_machine_stamp_is_read_correctly(self):
        with MrcFile(self.example_mrc_name) as mrc:
            assert np.array_equal(mrc.header.machst, [ 0x44, 0x41, 0, 0 ])
            if sys.byteorder == 'little':
                assert mrc.header.mode.dtype.byteorder in ('=', '<')
                assert mrc.data.dtype.byteorder in ('=', '<')
            else:
                assert mrc.header.mode.dtype.byteorder == '<'
                assert mrc.data.dtype.byteorder == '<'
    
    def test_non_mrc_file_is_rejected(self):
        name = os.path.join(self.test_data, 'emd_3197.png')
        with (self.assertRaisesRegexp(ValueError, 'Map ID string not found')):
            with MrcFile(name):
                pass
    
    def test_repr(self):
        with MrcFile(self.example_mrc_name) as mrc:
            expected = "MrcFile('{0}', mode='r')".format(self.example_mrc_name)
            assert repr(mrc) == expected
    
    def test_data_values_are_correct(self):
        with MrcFile(self.example_mrc_name) as mrc:
            # Check a few values
            self.assertAlmostEqual(mrc.data[0, 0, 0], -1.8013091)
            self.assertAlmostEqual(mrc.data[9, 6, 13], 4.6207790)
            self.assertAlmostEqual(mrc.data[9, 6, 14], 5.0373931)
            self.assertAlmostEqual(mrc.data[-1, -1, -1], 1.3078574)
            
            # Calculate some statistics for all values
            calc_max = mrc.data.max()
            calc_min = mrc.data.min()
            calc_mean = mrc.data.mean()
            calc_std = mrc.data.std()
            calc_sum = mrc.data.sum()
            
            # Compare calculated values with header records
            # TODO: check these values on different machines 
            self.assertAlmostEqual(calc_max, mrc.header.dmax)
            self.assertAlmostEqual(calc_min, mrc.header.dmin)
            self.assertAlmostEqual(calc_mean, mrc.header.dmean)
            self.assertAlmostEqual(calc_std, mrc.header.rms)
            self.assertAlmostEqual(calc_sum, 6268.8959961)
    
    def test_absent_extended_header_is_read_as_zero_length_array(self):
        with MrcFile(self.example_mrc_name) as mrc:
            assert mrc.header.nbytes == 1024
            assert mrc.header.nsymbt == 0
            assert mrc.extended_header.nbytes == 0
            assert mrc.extended_header.dtype.kind == 'V'
            assert str(mrc.extended_header.tobytes()) == ''
    
    def test_extended_header_is_read_correctly(self):
        name = os.path.join(self.test_data, 'EMD-3001.map')
        with MrcFile(name) as mrc:
            assert mrc.header.nbytes == 1024
            assert mrc.header.nsymbt == 160
            assert mrc.extended_header.nbytes == 160
            assert mrc.extended_header.dtype.kind == 'V'
            ext = str(mrc.extended_header)
            assert ext == ('X,  Y,  Z                               '
                           '                                        '
                           '-X,  Y+1/2,  -Z                         '
                           '                                        ')
    
    def test_cannot_edit_extended_header_in_read_only_mode(self):
        name = os.path.join(self.test_data, 'EMD-3001.map')
        with MrcFile(name, mode='r') as mrc:
            assert not mrc.extended_header.flags.writeable
            with self.assertRaisesRegexp(ValueError, 'read-only'):
                mrc.extended_header.fill('a')
    
    def test_cannot_set_extended_header_in_read_only_mode(self):
        with MrcFile(self.example_mrc_name, mode='r') as mrc:
            assert not mrc.extended_header.flags.writeable
            with self.assertRaisesRegexp(ValueError, 'read-only'):
                mrc.set_extended_header(np.zeros(5))
    
    def test_voxel_size_is_read_correctly(self):
        with MrcFile(self.example_mrc_name) as mrc:
            self.assertAlmostEqual(mrc.voxel_size.x, 11.400000, places=6)
            self.assertAlmostEqual(mrc.voxel_size.y, 11.400000, places=6)
            self.assertAlmostEqual(mrc.voxel_size.z, 11.400000, places=6)
    
    ############################################################################
    #
    # Tests which do not depend on any existing files
    #
    
    def test_cannot_accidentally_overwrite_file(self):
        assert not os.path.exists(self.temp_mrc_name)
        open(self.temp_mrc_name, 'w+').close()
        assert os.path.exists(self.temp_mrc_name)
        with self.assertRaises(IOError):
            MrcFile(self.temp_mrc_name, mode='w+')
    
    def test_can_deliberately_overwrite_file(self):
        assert not os.path.exists(self.temp_mrc_name)
        open(self.temp_mrc_name, 'w+').close()
        assert os.path.exists(self.temp_mrc_name)
        MrcFile(self.temp_mrc_name, mode='w+', overwrite=True).close()
    
    def test_can_edit_header_in_read_write_mode(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        with MrcFile(self.temp_mrc_name, mode='r+') as mrc:
            assert mrc.header.ispg == 0
            assert mrc.header.flags.writeable
            mrc.header.ispg = 1
            assert mrc.header.ispg == 1
    
    def test_cannot_edit_header_in_read_only_mode(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        with MrcFile(self.temp_mrc_name, mode='r') as mrc:
            assert mrc.header.ispg == 0
            assert not mrc.header.flags.writeable
            # TODO: the next line should raise an exception but numpy allows it
            # Bug reported: https://github.com/numpy/numpy/issues/8171 - should
            # be fixed in numpy > 1.11.2
            # For now we just make sure that the file itself is not altered
            mrc.header.ispg = 1
            assert mrc.header.ispg == 1
        with MrcFile(self.temp_mrc_name, mode='r') as mrc:
            assert mrc.header.ispg == 0
    
    def test_creating_extended_header(self):
        data = np.arange(12, dtype=np.int16).reshape(3, 4)
        extended_header = np.array('example extended header', dtype='S')
        with mrcfile.new(self.temp_mrc_name, data) as mrc:
            mrc.set_extended_header(extended_header)
            np.testing.assert_array_equal(mrc.data, data)
        with MrcFile(self.temp_mrc_name, mode='r') as mrc:
            # Change the extended header dtype to a string for comparison
            mrc.extended_header.dtype = 'S{}'.format(mrc.extended_header.nbytes)
            np.testing.assert_array_equal(mrc.extended_header, extended_header)
            np.testing.assert_array_equal(mrc.data, data)
    
    def test_removing_extended_header(self):
        data = np.arange(12, dtype=np.int16).reshape(3, 4)
        extended_header = np.array('example extended header', dtype='S')
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(data)
            mrc.set_extended_header(extended_header)
        with MrcFile(self.temp_mrc_name, mode='r+') as mrc:
            mrc.set_extended_header(np.array(()))
            assert mrc.header.nsymbt == 0
            mrc._file.seek(0, os.SEEK_END)
            file_size = mrc._file.tell()
            assert file_size == mrc.header.nbytes + mrc.data.nbytes
    
    def test_can_edit_data_in_read_write_mode(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        with MrcFile(self.temp_mrc_name, mode='r+') as mrc:
            assert mrc.data[1,1] == 5
            assert mrc.data.flags.writeable
            mrc.data[1,1] = 0
            assert mrc.data[1,1] == 0
    
    def test_data_array_cannot_be_changed_after_closing_file(self):
        mrc = MrcFile(self.temp_mrc_name, mode='w+')
        mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        data_ref = mrc.data
        # Check that writing to the data array does not raise an exception
        data_ref[0,0] = 1
        mrc.close()
        assert not data_ref.flags.writeable
        with self.assertRaises(ValueError):
            data_ref[0,0] = 2
    
    def test_cannot_edit_data_in_read_only_mode(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        with MrcFile(self.temp_mrc_name, mode='r') as mrc:
            assert mrc.data[1,1] == 5
            assert not mrc.data.flags.writeable
            with self.assertRaisesRegexp(ValueError, 'read-only'):
                mrc.data[1,1] = 0
    
    def test_2d_data_is_single_image(self):
        x, y = 3, 2
        data = np.arange(y * x, dtype=np.int16).reshape(y, x)
        with mrcfile.new(self.temp_mrc_name, data) as mrc:
            assert mrc.is_single_image()
            assert mrc.header.ispg == utils.IMAGE_STACK_SPACEGROUP
            assert mrc.header.nx == mrc.header.mx == x
            assert mrc.header.ny == mrc.header.my == y
            assert mrc.header.nz == mrc.header.mz == 1
    
    def test_switching_2d_data_to_image_stack_raises_exception(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(6, dtype=np.int16).reshape(2, 3))
            with self.assertRaises(ValueError):
                mrc.set_image_stack()
    
    def test_switching_2d_data_to_volume_raises_exception(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(6, dtype=np.int16).reshape(2, 3))
            with self.assertRaises(ValueError):
                mrc.set_volume()
    
    def test_3d_data_is_volume_by_default(self):
        x, y, z = 4, 3, 2
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(z * y * x, dtype=np.int16).reshape(z, y, x))
            assert mrc.is_volume()
            assert mrc.header.ispg == utils.VOLUME_SPACEGROUP
            assert mrc.header.nx == mrc.header.mx == x
            assert mrc.header.ny == mrc.header.my == y
            assert mrc.header.nz == mrc.header.mz == z
    
    def test_switching_volume_to_image_stack(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(2, 2, 3))
            assert mrc.is_volume()
            mrc.set_image_stack()
            assert mrc.is_image_stack()
            assert mrc.header.ispg == utils.IMAGE_STACK_SPACEGROUP
            assert mrc.header.nz == 2
            assert mrc.header.mz == 1
    
    def test_switching_image_stack_to_volume(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(2, 2, 3))
            assert mrc.is_volume()
            mrc.set_image_stack()
            assert mrc.is_image_stack()
            mrc.set_volume()
            assert mrc.is_volume()
            assert mrc.header.ispg == utils.VOLUME_SPACEGROUP
            assert mrc.header.nz == mrc.header.mz == 2
    
    def test_4d_data_is_volume_stack(self):
        x, y, z, nvol = 3, 4, 5, 6
        vstack = (np.arange(nvol * z * y * x, dtype=np.int16)
                  .reshape(nvol, z, y, x))
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(vstack)
            assert mrc.is_volume_stack()
            assert mrc.header.ispg == utils.VOLUME_STACK_SPACEGROUP
            assert mrc.header.nx == mrc.header.mx == x
            assert mrc.header.ny == mrc.header.my == y
            assert mrc.header.nz == z * nvol
            assert mrc.header.mz == z
    
    def test_switching_4d_data_to_image_stack_raises_exception(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(24, dtype=np.int16).reshape(2, 2, 2, 3))
            with self.assertRaises(ValueError):
                mrc.set_image_stack()
    
    def test_switching_4d_data_to_volume_raises_exception(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(24, dtype=np.int16).reshape(2, 2, 2, 3))
            with self.assertRaises(ValueError):
                mrc.set_volume()
    
    def test_writing_image_mode_0(self):
        x, y = 10, 9
        data = np.linspace(-128, 127, x * y, dtype=np.int8).reshape(y, x)
        name = os.path.join(self.test_output, 'test_img_10x9_mode0.mrc')
        
        # Write data
        with MrcFile(name, mode='w+') as mrc:
            mrc.set_data(data)
        
        # Re-read data and check header and data values
        with MrcFile(name) as mrc:
            np.testing.assert_array_equal(mrc.data, data)
            assert not mrc.is_image_stack()
            assert mrc.header.ispg == utils.IMAGE_STACK_SPACEGROUP
            assert mrc.header.nx == mrc.header.mx == x
            assert mrc.header.ny == mrc.header.my == y
            assert mrc.header.nz == mrc.header.mz == 1
    
    def test_writing_image_unsigned_bytes(self):
        x, y = 10, 9
        data = np.linspace(0, 255, x * y, dtype=np.uint8).reshape(y, x)
        name = os.path.join(self.test_output, 'test_img_10x9_uint8.mrc')
        
        # Write data
        with MrcFile(name, mode='w+') as mrc:
            mrc.set_data(data)
            
            # Check data has been converted to mode 6
            np.testing.assert_array_equal(mrc.data, data)
            assert mrc.header.mode == 6
            assert mrc.data.dtype == np.uint16
    
    def test_writing_image_mode_1_native_byte_order(self):
        data = np.linspace(-32768, 32767, 90, dtype=np.int16).reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode1_native.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_1_little_endian(self):
        data = np.linspace(-32768, 32767, 90, dtype='<i2').reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode1_le.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_1_big_endian(self):
        data = np.linspace(-32768, 32767, 90, dtype='>i2').reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode1_be.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_2_native_byte_order(self):
        data = create_test_float32_array()
        name = os.path.join(self.test_output, 'test_img_10x9_mode2_native.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_2_little_endian(self):
        data = create_test_float32_array(np.dtype('<f4'))
        name = os.path.join(self.test_output, 'test_img_10x9_mode2_le.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_2_big_endian(self):
        data = create_test_float32_array(np.dtype('>f4'))
        name = os.path.join(self.test_output, 'test_img_10x9_mode2_be.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_2_with_inf_and_nan(self):
        # Make an array of test data
        data = create_test_float32_array()
        
        # Set some unusual values
        data[4][0] = np.nan
        data[4][1] = np.inf
        data[4][2] = -np.inf
        
        # Write the data to a file and test it's read back correctly
        name = os.path.join(self.test_output, 'test_img_10x9_mode2_inf_nan.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_float16(self):
        x, y = 10, 9
        data = np.linspace(-65504, 65504, x * y, dtype=np.float16).reshape(y, x)
        name = os.path.join(self.test_output, 'test_img_10x9_float16.mrc')
        
        # Write data
        with MrcFile(name, mode='w+') as mrc:
            mrc.set_data(data)
            
            # Check data has been converted to mode 2
            np.testing.assert_array_equal(mrc.data, data)
            assert mrc.header.mode == 2
            assert mrc.data.dtype == np.float32
    
    def test_writing_image_mode_4_native_byte_order(self):
        data = create_test_complex64_array()
        name = os.path.join(self.test_output, 'test_img_10x9_mode4_native.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_4_little_endian(self):
        data = create_test_complex64_array().astype('<c8')
        name = os.path.join(self.test_output, 'test_img_10x9_mode4_le.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_4_big_endian(self):
        data = create_test_complex64_array().astype('>c8')
        name = os.path.join(self.test_output, 'test_img_10x9_mode4_be.mrc')
        # Suppress complex casting warnings from statistics calculations
        warnings.simplefilter('ignore', np.ComplexWarning)
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_4_with_inf_and_nan(self):
        # Make an array of test data
        data = create_test_complex64_array()
        
        # Set some unusual values
        data[4][0] = (0+0j) * np.nan # =(nan+nan*j)
        data[4][1] = (1+1j) * np.inf # =(inf+inf*j)
        data[4][2] = (-1-1j) * np.inf # =(-inf-inf*j)
        data[4][3] = (1-1j) * np.inf # =(inf-inf*j)
        data[4][4] = (-1+1j) * np.inf # =(-inf+inf*j)
        
        # Write the data to a file and test it's read back correctly
        name = os.path.join(self.test_output, 'test_img_10x9_mode4_inf_nan.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_6_native_byte_order(self):
        data = np.linspace(0, 65535, 90, dtype=np.int16).reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode6_native.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_6_little_endian(self):
        data = np.linspace(0, 65535, 90, dtype='<u2').reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode6_le.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_6_big_endian(self):
        data = np.linspace(0, 65535, 90, dtype='>u2').reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode6_be.mrc')
        write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_stack_mode_2_native_byte_order(self):
        x, y, z = 10, 9, 5
        img = np.linspace(-1e6, 1e6, x * y, dtype=np.float32).reshape(y, x)
        stack = np.arange(1, 6, dtype=np.float32).reshape(z, 1, 1) * img
        name = os.path.join(self.test_output, 'test_img_stack_10x9x5_mode2_native.mrc')
        
        # Write data
        with MrcFile(name, mode='w+') as mrc:
            mrc.set_data(stack)
            mrc.set_image_stack()
        
        # Re-read data and check header and data values
        with MrcFile(name) as mrc:
            np.testing.assert_array_equal(mrc.data, stack)
            assert mrc.is_image_stack()
            assert mrc.header.ispg == utils.IMAGE_STACK_SPACEGROUP
            assert mrc.header.nx == mrc.header.mx == x
            assert mrc.header.ny == mrc.header.my == y
            assert mrc.header.mz == 1
            assert mrc.header.nz == z
    
    def test_writing_volume_mode_1_native_byte_order(self):
        x, y, z = 10, 9, 5
        img = np.linspace(-32768, 32767, x * y, dtype=np.int16).reshape(y, x)
        vol = img // np.arange(1, 6, dtype=np.int16).reshape(z, 1, 1)
        name = os.path.join(self.test_output, 'test_vol_10x9x5_mode1_native.mrc')
        
        # Write data
        with MrcFile(name, mode='w+') as mrc:
            mrc.set_data(vol)
        
        # Re-read data and check header and data values
        with MrcFile(name) as mrc:
            np.testing.assert_array_equal(mrc.data, vol)
            assert mrc.header.ispg == utils.VOLUME_SPACEGROUP
            assert mrc.header.nx == mrc.header.mx == x
            assert mrc.header.ny == mrc.header.my == y
            assert mrc.header.mz == mrc.header.nz == z
    
    def test_writing_volume_stack_mode_1_native_byte_order(self):
        x, y, z, nvol = 10, 9, 5, 3
        img = np.linspace(-32768, 32767, x * y, dtype=np.int16).reshape(y, x)
        vol = img // np.arange(1, 6, dtype=np.int16).reshape(z, 1, 1)
        stack = vol * np.array([-1, 0, 1], dtype=np.int16).reshape(nvol, 1, 1, 1)
        name = os.path.join(self.test_output, 'test_vol_stack_10x9x5x3_mode1_native.mrc')
        
        # Write data
        with MrcFile(name, mode='w+') as mrc:
            mrc.set_data(stack)
        
        # Re-read data and check header and data values
        with MrcFile(name) as mrc:
            np.testing.assert_array_equal(mrc.data, stack)
            assert mrc.header.ispg == utils.VOLUME_STACK_SPACEGROUP
            assert mrc.header.nx == mrc.header.mx == x
            assert mrc.header.ny == mrc.header.my == y
            assert mrc.header.mz == z
            assert mrc.header.nz == z * nvol
    
    def test_new_header_stats_are_undetermined(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            assert mrc.header.dmax < mrc.header.dmin
            assert mrc.header.dmean < mrc.header.dmin
            assert mrc.header.dmean < mrc.header.dmax
            assert mrc.header.rms < 0
    
    def test_stats_are_updated_for_new_data(self):
        x, y, z = 10, 9, 5
        img = np.linspace(-32768, 32767, x * y, dtype=np.int16).reshape(y, x)
        vol = img // np.arange(1, 6, dtype=np.int16).reshape(z, 1, 1)
        
        # Write data
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(vol)
            assert mrc.header.dmin == np.float32(vol.min())
            assert mrc.header.dmax == np.float32(vol.max())
            assert mrc.header.dmean == np.float32(vol.mean(dtype=np.float64))
            assert mrc.header.rms == np.float32(vol.std(dtype=np.float64))
    
    def test_stats_are_updated_on_request(self):
        x, y = 4, 3
        zeros = np.zeros(x * y, dtype=np.int16).reshape(y, x)
        data = np.arange(x * y, dtype=np.int16).reshape(y, x)
        
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            # Write zeros to file
            mrc.set_data(zeros)
            
            # Now replace with non-zero data, in place
            mrc.data[:] = data[:]
            
            # Header values should have been set from the original zeros
            assert mrc.header.dmin == 0.0
            assert mrc.header.dmax == 0.0
            assert mrc.header.dmean == 0.0
            assert mrc.header.rms == 0.0
            
            # Now explicitly update the stats
            mrc.update_header_stats()
            assert mrc.header.dmin == np.float32(data.min())
            assert mrc.header.dmax == np.float32(data.max())
            assert mrc.header.dmean == np.float32(data.mean(dtype=np.float64))
            assert mrc.header.rms == np.float32(data.std(dtype=np.float64))
    
    def test_setting_voxel_size_as_single_number(self):
        x, y, z = 4, 3, 1
        data = np.arange(x * y, dtype=np.int16).reshape(z, y, x)
        
        with MrcFile(self.temp_mrc_name, 'w+') as mrc:
            mrc.set_data(data)
            assert mrc.voxel_size.x == 0.0
            assert mrc.voxel_size.y == 0.0
            assert mrc.voxel_size.z == 0.0
            
            voxel_size = 1.530
            mrc.voxel_size = voxel_size
            self.assertAlmostEqual(mrc.voxel_size.x, voxel_size, places=3)
            self.assertAlmostEqual(mrc.voxel_size.y, voxel_size, places=3)
            self.assertAlmostEqual(mrc.voxel_size.z, voxel_size, places=3)
    
    def test_setting_voxel_size_as_tuple(self):
        x, y, z = 4, 3, 1
        data = np.arange(x * y, dtype=np.int16).reshape(z, y, x)
        
        with MrcFile(self.temp_mrc_name, 'w+') as mrc:
            mrc.set_data(data)
            assert mrc.voxel_size.x == 0.0
            assert mrc.voxel_size.y == 0.0
            assert mrc.voxel_size.z == 0.0
            
            voxel_size = (1.1, 2.2, 3.3)
            mrc.voxel_size = voxel_size
            
            # Check the new (re-calculated) values
            self.assertAlmostEqual(mrc.voxel_size.x, voxel_size[0], places=3)
            self.assertAlmostEqual(mrc.voxel_size.y, voxel_size[1], places=3)
            self.assertAlmostEqual(mrc.voxel_size.z, voxel_size[2], places=3)
            
            # Also check the header values
            assert mrc.header.mx == 4
            assert mrc.header.my == 3
            assert mrc.header.mz == 1
            self.assertAlmostEqual(mrc.header.cella.x, 4.4, places=3)
            self.assertAlmostEqual(mrc.header.cella.y, 6.6, places=3)
            self.assertAlmostEqual(mrc.header.cella.z, 3.3, places=3)
    
    def test_setting_voxel_size_as_modified_array(self):
        x, y, z = 4, 3, 1
        data = np.arange(x * y, dtype=np.int16).reshape(z, y, x)
        
        with MrcFile(self.temp_mrc_name, 'w+') as mrc:
            mrc.set_data(data)
            assert mrc.voxel_size.x == 0.0
            assert mrc.voxel_size.y == 0.0
            assert mrc.voxel_size.z == 0.0
            
            voxel_size = mrc.voxel_size
            voxel_size.x = 1.1
            voxel_size.y = 2.2
            voxel_size.z = 3.3
            mrc.voxel_size = voxel_size
            self.assertAlmostEqual(mrc.voxel_size.x, 1.1, places=3)
            self.assertAlmostEqual(mrc.voxel_size.y, 2.2, places=3)
            self.assertAlmostEqual(mrc.voxel_size.z, 3.3, places=3)
    
    def test_new_header_contains_creator_label(self):
        with MrcFile(self.temp_mrc_name, mode='w+') as mrc:
            assert mrc.header.nlabl == 1
            label = mrc.header.label[0]
            assert label.startswith('Created by mrcfile.py    ')
            time = label[-40:].strip()
            datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    
    def test_header_dtype_is_correct_length(self):
        assert utils.HEADER_DTYPE.itemsize == 1024
    
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
            utils.mode_from_dtype(np.dtype([(b'f1', np.int32)]))

def write_file_then_read_and_assert_data_unchanged(name, data):
    with MrcFile(name, mode='w+') as mrc:
        mrc.set_data(data)
    with MrcFile(name) as mrc:
        np.testing.assert_array_equal(mrc.data, data)
        assert mrc.data.dtype == data.dtype

def create_test_float32_array(dtype=np.float32):
    """Create a 10 x 9 array of float values over almost all of float32 range"""
    data = np.zeros((9, 10), dtype=dtype)
    data[:4] = np.negative(np.logspace(38.5, -38.5, 40).reshape(4, 10))
    data[5:] = np.logspace(-38.5, 38.5, 40).reshape(4, 10)
    return data

def create_test_complex64_array():
    floats = create_test_float32_array()
    data = 1j * floats[::-1]
    data += floats
    assert data.dtype.type == np.complex64
    return data

if __name__ == '__main__':
    unittest.main()
