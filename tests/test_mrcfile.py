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

import numpy as np

from . import helpers
from .test_mrcobject import MrcObjectTest
from mrcfile.mrcfile import MrcFile
from mrcfile.mrcobject import (IMAGE_STACK_SPACEGROUP, VOLUME_SPACEGROUP,
                               VOLUME_STACK_SPACEGROUP)
import mrcfile.utils as utils


# Doctest stuff commented out for now - would be nice to get it working!
# import doctest

# doc_test_dir = tempfile.mkdtemp()
# doc_test_file = MrcFile(os.path.join(doc_test_dir, 'doc_test.mrc'), 'w+')
# 
# def tearDownModule():
#     global doc_test_dir, doc_test_file
#     doc_test_file.close()
#     if os.path.exists(doc_test_dir):
#         shutil.rmtree(doc_test_dir)
# 
# def load_tests(loader, tests, ignore):
#     global doc_test_file
#     tests.addTests(doctest.DocTestSuite(mrcfile, extraglobs={'mrc': doc_test_file}))
#     return tests


class MrcFileTest(MrcObjectTest):
    
    """Unit tests for MRC file I/O.
    
    Note that this test class inherits MrcObjectTest to ensure all of the tests
    for MrcObject work correctly for the MrcFile subclass. setUp() is a little
    more complicated as a result.
    
    """
    
    def setUp(self):
        super(MrcFileTest, self).setUp()
        
        # Set up test files and names to be used
        self.test_data = helpers.get_test_data_path()
        self.test_output = tempfile.mkdtemp()
        self.temp_mrc_name = os.path.join(self.test_output, 'test_mrcfile.mrc')
        self.example_mrc_name = os.path.join(self.test_data, 'EMD-3197.map')
        self.ext_header_mrc_name = os.path.join(self.test_data, 'EMD-3001.map')
        self.fei_ext_header_mrc_name = os.path.join(self.test_data, 'fei-extended.mrc')
        
        # Set newmrc method as MrcFile constructor, to allow override by subclasses
        self.newmrc = MrcFile
        
        # Set up parameters so MrcObject tests run on the MrcFile class
        obj_mrc_name = os.path.join(self.test_output, 'test_mrcobject.mrc')
        self.mrcobject = MrcFile(obj_mrc_name, 'w+')
    
    def tearDown(self):
        self.mrcobject.close()
        if os.path.exists(self.test_output):
            shutil.rmtree(self.test_output)
        super(MrcFileTest, self).tearDown()
    
    ############################################################################
    #
    # Tests which depend on existing files (in the test_data directory)
    #
    
    def test_machine_stamp_is_read_correctly(self):
        with self.newmrc(self.example_mrc_name) as mrc:
            assert np.array_equal(mrc.header.machst, [ 0x44, 0x41, 0, 0 ])
            if sys.byteorder == 'little':
                assert mrc.header.mode.dtype.byteorder in ('=', '<')
                assert mrc.data.dtype.byteorder in ('=', '<')
            else:
                assert mrc.header.mode.dtype.byteorder == '<'
                assert mrc.data.dtype.byteorder == '<'
    
    def test_non_mrc_file_is_rejected(self):
        name = os.path.join(self.test_data, 'emd_3197.png')
        with (self.assertRaisesRegex(ValueError, 'Map ID string not found')):
            self.newmrc(name)
    
    def test_non_mrc_file_gives_correct_warnings_in_permissive_mode(self):
        name = os.path.join(self.test_data, 'emd_3197.png')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.newmrc(name, permissive=True)
            assert len(w) == 3
            assert "Map ID string not found" in str(w[0].message)
            assert "Unrecognised machine stamp" in str(w[1].message)
            assert "Unrecognised mode" in str(w[2].message)
    
    def test_repr(self):
        with self.newmrc(self.example_mrc_name) as mrc:
            expected = "MrcFile('{0}', mode='r')".format(self.example_mrc_name)
            assert repr(mrc) == expected
    
    def test_data_values_are_correct(self):
        with self.newmrc(self.example_mrc_name) as mrc:
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
            self.assertAlmostEqual(calc_max, mrc.header.dmax)
            self.assertAlmostEqual(calc_min, mrc.header.dmin)
            self.assertAlmostEqual(calc_mean, mrc.header.dmean)
            self.assertAlmostEqual(calc_std, mrc.header.rms)
            
            # Convert calc_sum to float to fix a bug with memmap comparisons in python 3
            self.assertAlmostEqual(float(calc_sum), 6268.8959961)
    
    def test_absent_extended_header_is_read_as_zero_length_array(self):
        with self.newmrc(self.example_mrc_name) as mrc:
            assert mrc.header.nbytes == 1024
            assert mrc.header.nsymbt == 0
            assert mrc.extended_header.nbytes == 0
            assert mrc.extended_header.dtype.kind == 'V'
            assert mrc.extended_header.tobytes() == b''
    
    def test_extended_header_is_read_correctly(self):
        with self.newmrc(self.ext_header_mrc_name) as mrc:
            assert mrc.header.nbytes == 1024
            assert mrc.header.nsymbt == 160
            assert mrc.extended_header.nbytes == 160
            assert mrc.extended_header.dtype.kind == 'V'
            mrc.extended_header.dtype = 'S80'
            ext = mrc.extended_header
            assert ext[0] == (b'X,  Y,  Z                               '
                              b'                                        ')
            assert ext[1] == (b'-X,  Y+1/2,  -Z                         '
                              b'                                        ')
    
    def test_extended_header_from_FEI_file(self):
        with self.newmrc(self.fei_ext_header_mrc_name) as mrc:
            # FEI1 means use the fei format
            assert mrc.header['exttyp'] == b'FEI1'
            assert mrc.header.nsymbt == 786432
            ext = mrc.extended_header
            assert ext.nbytes == 786432
            assert ext.dtype.kind == 'V'
            assert ext.dtype['Metadata size'] == np.dtype('|i')
            assert ext.dtype['Microscope type'] == np.dtype('|S16')
            assert ext[0]['Metadata size'] == 768
            assert ext[0]['Microscope type'] == b'TITAN52336320'
            assert ext[0]['HT'] == 300000.0
    
    def test_cannot_edit_extended_header_in_read_only_mode(self):
        with self.newmrc(self.ext_header_mrc_name, mode='r') as mrc:
            assert not mrc.extended_header.flags.writeable
            with self.assertRaisesRegex(ValueError, 'read-only'):
                mrc.extended_header.fill(b'a')
    
    def test_cannot_set_extended_header_in_read_only_mode(self):
        with self.newmrc(self.example_mrc_name, mode='r') as mrc:
            assert not mrc.extended_header.flags.writeable
            with self.assertRaisesRegex(ValueError, 'read-only'):
                mrc.set_extended_header(np.zeros(5))
    
    def test_voxel_size_is_read_correctly(self):
        with self.newmrc(self.example_mrc_name) as mrc:
            self.assertAlmostEqual(mrc.voxel_size.x, 11.400000, places=6)
            self.assertAlmostEqual(mrc.voxel_size.y, 11.400000, places=6)
            self.assertAlmostEqual(mrc.voxel_size.z, 11.400000, places=6)
    
    def test_stream_can_be_read_again(self):
        with self.newmrc(self.example_mrc_name) as mrc:
            orig_data = mrc.data.copy()
            mrc._read()
            np.testing.assert_array_equal(orig_data, mrc.data)
    
    ############################################################################
    #
    # Tests which do not depend on any existing files
    #
    
    def test_opening_nonexistent_file(self):
        with self.assertRaisesRegex(Exception, "No such file"):
            self.newmrc('no_file')
    
    def test_opening_file_with_unknown_mode(self):
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.header.mode = 10
        with self.assertRaisesRegex(ValueError, "Unrecognised mode"):
            self.newmrc(self.temp_mrc_name)
    
    def test_can_read_and_flush_stream_repeatedly(self):
        orig_data = np.arange(12, dtype=np.int16).reshape(3, 4)
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(orig_data.copy())
            mrc.flush()
            np.testing.assert_array_equal(orig_data, mrc.data)
            mrc._read()
            np.testing.assert_array_equal(orig_data, mrc.data)
            mrc._read()
            mrc.flush()
            mrc.flush()
            mrc._read()
            mrc._read()
            mrc.flush()
            np.testing.assert_array_equal(orig_data, mrc.data)
    
    def test_cannot_use_invalid_file_modes(self):
        for mode in ('w', 'a', 'a+'):
            with self.assertRaisesRegex(ValueError, "Mode '.+' not supported"):
                self.newmrc(self.temp_mrc_name, mode=mode)
    
    def test_cannot_accidentally_overwrite_file(self):
        assert not os.path.exists(self.temp_mrc_name)
        open(self.temp_mrc_name, 'w+').close()
        assert os.path.exists(self.temp_mrc_name)
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.newmrc(self.temp_mrc_name, mode='w+')
    
    def test_can_deliberately_overwrite_file(self):
        assert not os.path.exists(self.temp_mrc_name)
        open(self.temp_mrc_name, 'w+').close()
        assert os.path.exists(self.temp_mrc_name)
        self.newmrc(self.temp_mrc_name, mode='w+', overwrite=True).close()
    
    def test_warning_issued_if_file_is_too_large(self):
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
            # Call internal _set_new_data() method to add an extra row of data
            # without updating the header
            mrc._set_new_data(np.arange(16, dtype=np.int16).reshape(4, 4))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.newmrc(self.temp_mrc_name)
            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)
            assert "file is 8 bytes larger than expected" in str(w[0].message)
    
    def test_exception_raised_if_file_is_too_small(self):
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(24, dtype=np.int16).reshape(2, 3, 4))
            assert mrc.header.mz == 2
            mrc.header.mz = mrc.header.nz = 3
        expected_error_msg = ("Expected 72 bytes in data block "
                              "but could only read 48")
        with self.assertRaisesRegex(ValueError, expected_error_msg):
            self.newmrc(self.temp_mrc_name)
    
    def test_can_edit_header_in_read_write_mode(self):
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        with self.newmrc(self.temp_mrc_name, mode='r+') as mrc:
            assert mrc.header.ispg == 0
            assert mrc.header.flags.writeable
            mrc.header.ispg = 1
            assert mrc.header.ispg == 1
    
    def test_cannot_edit_header_in_read_only_mode(self):
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        with self.newmrc(self.temp_mrc_name, mode='r') as mrc:
            assert mrc.header.ispg == 0
            assert not mrc.header.flags.writeable
            if np.__version__[:4] == '1.11':
                # The next line should raise an exception but numpy 1.11 allows
                # it, so we open the file again below and test that the file
                # itself was not altered.
                mrc.header.ispg = 1
                assert mrc.header.ispg == 1
            else:
                # The bug was fixed in numpy 1.12 so we test that properly
                with self.assertRaisesRegex(ValueError, 'read-only'):
                    mrc.header.ispg = 1
        with self.newmrc(self.temp_mrc_name, mode='r') as mrc:
            assert mrc.header.ispg == 0
    
    def test_creating_extended_header(self):
        data = np.arange(12, dtype=np.int16).reshape(3, 4)
        extended_header = np.array('example extended header', dtype='S')
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(data)
            mrc.set_extended_header(extended_header)
            np.testing.assert_array_equal(mrc.data, data)
        with self.newmrc(self.temp_mrc_name, mode='r') as mrc:
            # Change the extended header dtype to a string for comparison
            mrc.extended_header.dtype = 'S{}'.format(mrc.extended_header.nbytes)
            np.testing.assert_array_equal(mrc.extended_header, extended_header)
            np.testing.assert_array_equal(mrc.data, data)
    
    def test_removing_extended_header(self):
        data = np.arange(12, dtype=np.int16).reshape(3, 4)
        extended_header = np.array('example extended header', dtype='S')
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(data)
            mrc.set_extended_header(extended_header)
        with self.newmrc(self.temp_mrc_name, mode='r+') as mrc:
            mrc.set_extended_header(np.array(()))
            mrc.flush()
            assert mrc.header.nsymbt == 0
            file_size = mrc._iostream.tell() # relies on flush() leaving stream at end
            assert file_size == mrc.header.nbytes + mrc.data.nbytes

    def test_extended_header_with_incorrect_type(self):
        data = np.arange(12, dtype=np.int16).reshape(3, 4)
        extended_header = np.array('example extended header', dtype='S')
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(data)
            mrc.set_extended_header(extended_header)
            mrc.header.exttyp = b'FEI1'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with self.newmrc(self.temp_mrc_name, mode='r+') as mrc:
                # Test that the file is still read, and the dtype falls back to 'V'
                assert mrc.extended_header.dtype.kind == 'V'
                mrc.extended_header.dtype = 'S{}'.format(mrc.extended_header.nbytes)
                np.testing.assert_array_equal(mrc.extended_header, extended_header)
            assert len(w) == 1
            assert "FEI1" in str(w[0].message)
            assert "extended header" in str(w[0].message)
    
    def test_can_edit_data_in_read_write_mode(self):
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        with self.newmrc(self.temp_mrc_name, mode='r+') as mrc:
            assert mrc.data[1,1] == 5
            assert mrc.data.flags.writeable
            mrc.data[1,1] = 0
            assert mrc.data[1,1] == 0

    def test_cannot_edit_data_in_read_only_mode(self):
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        with self.newmrc(self.temp_mrc_name, mode='r') as mrc:
            assert mrc.data[1,1] == 5
            assert not mrc.data.flags.writeable
            with self.assertRaisesRegex(ValueError, 'read-only'):
                mrc.data[1,1] = 0
    
    def test_header_only_mode_does_not_read_data(self):
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(np.arange(12, dtype=np.int16).reshape(3, 4))
        with self.newmrc(self.temp_mrc_name, mode='r', header_only=True) as mrc:
            assert mrc.header is not None
            assert mrc.extended_header is not None
            assert mrc.data is None

    def test_writing_image_mode_0(self):
        x, y = 10, 9
        data = np.linspace(-128, 127, x * y, dtype=np.int8).reshape(y, x)
        name = os.path.join(self.test_output, 'test_img_10x9_mode0.mrc')
        
        # Write data
        with self.newmrc(name, mode='w+') as mrc:
            mrc.set_data(data)
        
        # Re-read data and check header and data values
        with self.newmrc(name) as mrc:
            np.testing.assert_array_equal(mrc.data, data)
            assert not mrc.is_image_stack()
            assert mrc.header.ispg == IMAGE_STACK_SPACEGROUP
            assert mrc.header.nx == mrc.header.mx == x
            assert mrc.header.ny == mrc.header.my == y
            assert mrc.header.nz == mrc.header.mz == 1
    
    def test_writing_image_unsigned_bytes(self):
        x, y = 10, 9
        data = np.linspace(0, 255, x * y, dtype=np.uint8).reshape(y, x)
        name = os.path.join(self.test_output, 'test_img_10x9_uint8.mrc')
        
        # Write data
        with self.newmrc(name, mode='w+') as mrc:
            mrc.set_data(data)
            
            # Check data has been converted to mode 6
            np.testing.assert_array_equal(mrc.data, data)
            assert mrc.header.mode == 6
            assert mrc.data.dtype == np.uint16
    
    def write_file_then_read_and_assert_data_unchanged(self, name, data):
        with self.newmrc(name, mode='w+') as mrc:
            mrc.set_data(data)
        with self.newmrc(name) as mrc:
            np.testing.assert_array_equal(mrc.data, data)
            assert mrc.data.dtype == data.dtype
    
    def test_writing_image_mode_1_native_byte_order(self):
        data = np.linspace(-32768, 32767, 90, dtype=np.int16).reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode1_native.mrc')
        self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_1_little_endian(self):
        data = np.linspace(-32768, 32767, 90, dtype='<i2').reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode1_le.mrc')
        self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_1_big_endian(self):
        data = np.linspace(-32768, 32767, 90, dtype='>i2').reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode1_be.mrc')
        self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_2_native_byte_order(self):
        data = create_test_float32_array()
        name = os.path.join(self.test_output, 'test_img_10x9_mode2_native.mrc')
        self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_2_little_endian(self):
        data = create_test_float32_array(np.dtype('<f4'))
        name = os.path.join(self.test_output, 'test_img_10x9_mode2_le.mrc')
        self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_2_big_endian(self):
        data = create_test_float32_array(np.dtype('>f4'))
        name = os.path.join(self.test_output, 'test_img_10x9_mode2_be.mrc')
        self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_2_with_inf_and_nan(self):
        # Make an array of test data
        data = create_test_float32_array()
        
        # Set some unusual values
        data[4][0] = np.nan
        data[4][1] = np.inf
        data[4][2] = -np.inf
        
        # Write the data to a file and test it's read back correctly
        name = os.path.join(self.test_output, 'test_img_10x9_mode2_inf_nan.mrc')
        # Suppress warnings from statistics calculations with inf and nan
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_float16(self):
        x, y = 10, 9
        data = np.linspace(-65504, 65504, x * y, dtype=np.float16).reshape(y, x)
        name = os.path.join(self.test_output, 'test_img_10x9_float16.mrc')
        
        # Write data
        with self.newmrc(name, mode='w+') as mrc:
            mrc.set_data(data)
            
            # Check data has been converted to mode 2
            np.testing.assert_array_equal(mrc.data, data)
            assert mrc.header.mode == 2
            assert mrc.data.dtype == np.float32
    
    def test_writing_image_mode_4_native_byte_order(self):
        data = create_test_complex64_array()
        name = os.path.join(self.test_output, 'test_img_10x9_mode4_native.mrc')
        # Suppress complex casting warnings from statistics calculations
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", np.ComplexWarning)
            self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_4_little_endian(self):
        data = create_test_complex64_array().astype('<c8')
        name = os.path.join(self.test_output, 'test_img_10x9_mode4_le.mrc')
        # Suppress complex casting warnings from statistics calculations
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", np.ComplexWarning)
            self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_4_big_endian(self):
        data = create_test_complex64_array().astype('>c8')
        name = os.path.join(self.test_output, 'test_img_10x9_mode4_be.mrc')
        # Suppress complex casting warnings from statistics calculations
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", np.ComplexWarning)
            self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_4_with_inf_and_nan(self):
        # Make an array of test data
        data = create_test_complex64_array()
        
        # Set some unusual values
        data[4][0] = (0 + 0j) * np.nan   # =(nan+nan*j)
        data[4][1] = (1 + 1j) * np.inf   # =(inf+inf*j)
        data[4][2] = (-1 - 1j) * np.inf  # =(-inf-inf*j)
        data[4][3] = (1 - 1j) * np.inf   # =(inf-inf*j)
        data[4][4] = (-1 + 1j) * np.inf  # =(-inf+inf*j)
        
        # Write the data to a file and test it's read back correctly
        name = os.path.join(self.test_output, 'test_img_10x9_mode4_inf_nan.mrc')
        # Suppress warnings from statistics calculations with inf and nan
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_6_native_byte_order(self):
        data = np.linspace(0, 65535, 90, dtype=np.int16).reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode6_native.mrc')
        self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_6_little_endian(self):
        data = np.linspace(0, 65535, 90, dtype='<u2').reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode6_le.mrc')
        self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_mode_6_big_endian(self):
        data = np.linspace(0, 65535, 90, dtype='>u2').reshape(9, 10)
        name = os.path.join(self.test_output, 'test_img_10x9_mode6_be.mrc')
        self.write_file_then_read_and_assert_data_unchanged(name, data)
    
    def test_writing_image_stack_mode_2_native_byte_order(self):
        x, y, z = 10, 9, 5
        img = np.linspace(-1e6, 1e6, x * y, dtype=np.float32).reshape(y, x)
        stack = np.arange(1, 6, dtype=np.float32).reshape(z, 1, 1) * img
        name = os.path.join(self.test_output, 'test_img_stack_10x9x5_mode2_native.mrc')
        
        # Write data
        with self.newmrc(name, mode='w+') as mrc:
            mrc.set_data(stack)
            mrc.set_image_stack()
        
        # Re-read data and check header and data values
        with self.newmrc(name) as mrc:
            np.testing.assert_array_equal(mrc.data, stack)
            assert mrc.is_image_stack()
            assert mrc.header.ispg == IMAGE_STACK_SPACEGROUP
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
        with self.newmrc(name, mode='w+') as mrc:
            mrc.set_data(vol)
        
        # Re-read data and check header and data values
        with self.newmrc(name) as mrc:
            np.testing.assert_array_equal(mrc.data, vol)
            assert mrc.header.ispg == VOLUME_SPACEGROUP
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
        with self.newmrc(name, mode='w+') as mrc:
            mrc.set_data(stack)
        
        # Re-read data and check header and data values
        with self.newmrc(name) as mrc:
            np.testing.assert_array_equal(mrc.data, stack)
            assert mrc.header.ispg == VOLUME_STACK_SPACEGROUP
            assert mrc.header.nx == mrc.header.mx == x
            assert mrc.header.ny == mrc.header.my == y
            assert mrc.header.mz == z
            assert mrc.header.nz == z * nvol
    
    def test_data_transposed_in_place_is_written_without_errors(self):
        # Quite unlikely that anyone will mess with the data array like this,
        # but still worth making sure the flush() call is robust!
        x, y, z = 10, 9, 5
        img = np.linspace(-32768, 32767, x * y, dtype=np.int16).reshape(y, x)
        vol = img // np.arange(1, 6, dtype=np.int16).reshape(z, 1, 1)
        transposed_vol = vol.transpose()
        
        # Write data and confirm it's C-contiguous
        mrc = self.newmrc(self.temp_mrc_name, mode='w+')
        mrc.set_data(vol)
        mrc.flush()
        assert mrc.data.flags.c_contiguous == True
        
        # Transpose the data array in-place
        strides = mrc.data.strides
        mrc.data.shape = mrc.data.shape[::-1]
        mrc.data.strides = strides[::-1]
        # Check this is an effective way to do in-place transpose()
        np.testing.assert_array_equal(transposed_vol, mrc.data)
        
        # Confirm data is no longer C-contiguous
        assert mrc.data.flags.c_contiguous == False
        
        # Flush and close should work without errors
        mrc.flush()
        mrc.close()
    
    def test_transposed_data_is_made_contiguous_on_set(self):
        # Quite unlikely that anyone will mess with the data array like this,
        # but still worth making sure the flush() call is robust!
        x, y, z = 10, 9, 5
        img = np.linspace(-32768, 32767, x * y, dtype=np.int16).reshape(y, x)
        vol = img // np.arange(1, 6, dtype=np.int16).reshape(z, 1, 1)
        vol = vol.transpose()
        
        assert vol.flags.c_contiguous == False
        
        # Write data and confirm it's C-contiguous
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(vol)
            assert mrc.data.flags.c_contiguous == True

    def test_permissive_read_with_wrong_machine_stamp(self):
        data = np.arange(12, dtype=np.int16).reshape(3, 4)
        with self.newmrc(self.temp_mrc_name, mode='w+') as mrc:
            mrc.set_data(data)
            wrong_byte_order = mrc.header.mode.newbyteorder().dtype.byteorder
            mrc.header.machst = utils.machine_stamp_from_byte_order(wrong_byte_order)
        with self.assertRaisesRegex(ValueError, "Unrecognised mode"):
            self.newmrc(self.temp_mrc_name)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with self.newmrc(self.temp_mrc_name, permissive=True) as mrc:
                np.testing.assert_array_equal(mrc.data, data)
            assert len(w) == 1
            assert "Machine stamp" in str(w[0].message)
            assert "byte order" in str(w[0].message)




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
