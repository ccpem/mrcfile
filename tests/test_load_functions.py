# Copyright (c) 2018, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for mrcfile __init__.py loading functions.
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import mmap
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

import mrcfile
from mrcfile.bzip2mrcfile import Bzip2MrcFile
from mrcfile.gzipmrcfile import GzipMrcFile
from . import helpers

# Try to import pathlib if we can
pathlib_unavailable = False
try:
    from pathlib import Path
except ImportError:
    try:
        from pathlib2 import Path
    except ImportError:
        pathlib_unavailable = True


class LoadFunctionTest(helpers.AssertRaisesRegexMixin, unittest.TestCase):
    
    """Unit tests for MRC loading functions.
    
    """
    
    def setUp(self):
        super(LoadFunctionTest, self).setUp()
        
        # Set up test files and names to be used
        self.test_data = helpers.get_test_data_path()
        self.test_output = tempfile.mkdtemp()
        self.temp_mrc_name = os.path.join(self.test_output, 'test_mrcfile.mrc')
        self.temp_gz_mrc_name = self.temp_mrc_name + '.gz'
        self.example_mrc_name = os.path.join(self.test_data, 'EMD-3197.map')
        self.gzip_mrc_name = os.path.join(self.test_data, 'emd_3197.map.gz')
        self.bzip2_mrc_name = os.path.join(self.test_data, 'EMD-3197.map.bz2')
        self.slow_mrc_name = os.path.join(self.test_data, 'fei-extended.mrc.gz')
    
    def tearDown(self):
        if os.path.exists(self.test_output):
            shutil.rmtree(self.test_output)
        super(LoadFunctionTest, self).tearDown()
    
    def test_normal_opening(self):
        with mrcfile.open(self.example_mrc_name) as mrc:
            assert repr(mrc) == ("MrcFile('{0}', mode='r')"
                                 .format(self.example_mrc_name))

    @unittest.skipIf(pathlib_unavailable, "pathlib not available")
    def test_normal_opening_pathlib(self):
        """Single test to ensure pathlib functionality is tested even if there's
        a problem with the LoadFunctionTestWithPathlib class"""
        path = Path(self.example_mrc_name)
        with mrcfile.open(path) as mrc:
            assert repr(mrc) == ("MrcFile('{0}', mode='r')"
                                 .format(self.example_mrc_name))

    def test_read(self):
        volume = mrcfile.read(self.example_mrc_name)
        assert isinstance(volume, np.ndarray)
        assert volume.shape, volume.dtype == ((20, 20, 20), np.float32)
        assert volume.flags.writeable is True
    
    def test_gzip_opening(self):
        with mrcfile.open(self.gzip_mrc_name) as mrc:
            assert repr(mrc) == ("GzipMrcFile('{0}', mode='r')"
                                 .format(self.gzip_mrc_name))
    
    def test_bzip2_opening(self):
        with mrcfile.open(self.bzip2_mrc_name) as mrc:
            assert repr(mrc) == ("Bzip2MrcFile('{0}', mode='r')"
                                 .format(self.bzip2_mrc_name))
    
    def test_mmap_opening(self):
        with mrcfile.mmap(self.example_mrc_name) as mrc:
            assert repr(mrc) == ("MrcMemmap('{0}', mode='r')"
                                 .format(self.example_mrc_name))
    
    def test_new_empty_file(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            assert repr(mrc) == ("MrcFile('{0}', mode='w+')"
                                 .format(self.temp_mrc_name))

    def test_new_empty_file_with_open_function(self):
        with mrcfile.open(self.temp_mrc_name, mode='w+') as mrc:
            assert repr(mrc) == ("MrcFile('{0}', mode='w+')"
                                 .format(self.temp_mrc_name))

    def test_error_overwriting_file_with_open_function(self):
        # Convert name to str to avoid TypeErrors in Python 2.7 with pathlib
        temp_mrc_name_str = str(self.temp_mrc_name)
        assert not os.path.exists(temp_mrc_name_str)
        open(temp_mrc_name_str, 'w+').close()
        assert os.path.exists(temp_mrc_name_str)
        with self.assertRaisesRegex(ValueError, r"call 'mrcfile\.new\(\)'"):
            mrcfile.open(self.temp_mrc_name, mode='w+')

    def test_header_only_opening(self):
        with mrcfile.open(self.example_mrc_name, header_only=True) as mrc:
            assert mrc.header is not None
            assert mrc.extended_header is not None
            assert mrc.data is None
    
    def test_opening_nonexistent_file(self):
        with self.assertRaisesRegex(Exception, "No such file"):
            mrcfile.open('no_file')
    
    def test_new_file_with_data(self):
        data = np.arange(24, dtype=np.uint16).reshape(2, 3, 4)
        with mrcfile.new(self.temp_mrc_name, data) as mrc:
            np.testing.assert_array_equal(data, mrc.data)
    
    def test_new_gzip_file(self):
        data = np.arange(24, dtype=np.uint16).reshape(4, 3, 2)
        with mrcfile.new(self.temp_mrc_name, data, compression='gzip') as mrc:
            np.testing.assert_array_equal(data, mrc.data)
            assert repr(mrc) == ("GzipMrcFile('{0}', mode='w+')"
                                 .format(self.temp_mrc_name))
    
    def test_new_bzip2_file(self):
        data = np.arange(24, dtype=np.uint16).reshape(4, 3, 2)
        with mrcfile.new(self.temp_mrc_name, data, compression='bzip2') as mrc:
            np.testing.assert_array_equal(data, mrc.data)
            assert repr(mrc) == ("Bzip2MrcFile('{0}', mode='w+')"
                                 .format(self.temp_mrc_name))
    
    def test_unknown_compression_type(self):
        with self.assertRaisesRegex(ValueError, 'Unknown compression format'):
            mrcfile.new(self.temp_mrc_name, compression='other')
    
    def test_overwriting_flag(self):
        assert not os.path.exists(str(self.temp_mrc_name))
        open(str(self.temp_mrc_name), 'w+').close()
        assert os.path.exists(str(self.temp_mrc_name))
        with self.assertRaisesRegex(ValueError, "already exists"):
            mrcfile.new(self.temp_mrc_name)
        with self.assertRaisesRegex(ValueError, "already exists"):
            mrcfile.new(self.temp_mrc_name, overwrite=False)
        mrcfile.new(self.temp_mrc_name, overwrite=True).close()
    
    def test_invalid_mode_raises_exception(self):
        with self.assertRaisesRegex(ValueError, "Mode 'z' not supported"):
            mrcfile.open(self.example_mrc_name, mode='z')
    
    def test_non_mrc_file_raises_exception(self):
        name = os.path.join(self.test_data, 'emd_3197.png')
        with self.assertRaisesRegex(ValueError, 'Map ID string not found'):
            mrcfile.open(name)
    
    def test_gzipped_non_mrc_file_raises_exception(self):
        name = os.path.join(self.test_data, 'emd_3197.png.gz')
        with self.assertRaisesRegex(ValueError, 'Map ID string not found'):
            mrcfile.open(name)
    
    def test_error_in_gzip_opening_raises_new_exception(self):
        # Tricky to test this case. Easiest to monkey-patch GzipMrcFile.__init__
        old_init = GzipMrcFile.__init__
        try:
            msg = 'Fake error: valid gzip file with invalid MRC data'
            def error(*args, **kwargs):
                raise IOError(msg)
            GzipMrcFile.__init__ = error
            with self.assertRaisesRegex(IOError, msg):
                mrcfile.open(self.gzip_mrc_name)
        finally:
            GzipMrcFile.__init__ = old_init
    
    def test_error_in_bzip2_opening_raises_new_exception(self):
        # Tricky to test this case. Easiest to monkey-patch Bzip2MrcFile.__init__
        old_init = Bzip2MrcFile.__init__
        try:
            msg = 'Fake error: valid bzip2 file with invalid MRC data'
            def error(*args, **kwargs):
                raise IOError(msg)
            Bzip2MrcFile.__init__ = error
            with self.assertRaisesRegex(IOError, msg):
                mrcfile.open(self.bzip2_mrc_name)
        finally:
            Bzip2MrcFile.__init__ = old_init
    
    def test_switching_mode(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(np.arange(12, dtype=np.int8).reshape(3, 4))
        with mrcfile.open(self.temp_mrc_name, mode='r+') as mrc:
            mrc.set_data(np.arange(20, dtype=np.int16).reshape(2, 2, 5))
            assert mrc.header.mode == 1

    def test_simple_async_opening(self):
        with mrcfile.open_async(self.example_mrc_name).result() as mrc:
            assert repr(mrc) == ("MrcFile('{0}', mode='r')"
                                 .format(self.example_mrc_name))

    def test_slow_async_opening(self):
        # This test relies on the fact that file opening takes longer than the
        # assertions tested immediately after the open_async() call. It seems
        # to work well even with the small gzip or bzip2 files, but we use a
        # much larger gzip file to make sure.
        future = mrcfile.open_async(self.slow_mrc_name)
        assert future.running()
        assert not future.done()
        with future.result() as mrc:
            assert future.done()
            assert not future.running()
            assert repr(mrc) == ("GzipMrcFile('{0}', mode='r')"
                                 .format(self.slow_mrc_name))
        assert future.exception() is None

    def test_new_mmap(self):
        with mrcfile.new_mmap(self.temp_mrc_name,
                              (3, 4, 5, 6),
                              mrc_mode=2,
                              fill=1.1) as mrc:
            assert repr(mrc) == ("MrcMemmap('{0}', mode='w+')"
                                 .format(self.temp_mrc_name))
            assert mrc.data.shape == (3, 4, 5, 6)
            assert np.all(mrc.data == 1.1)
            assert mrc.header.nx == 6
            mrc._iostream.seek(0, os.SEEK_END)
            file_size = mrc._iostream.tell()
            assert file_size == mrc.header.nbytes + mrc.data.nbytes

    def test_new_mmap_with_extended_header(self):
        with mrcfile.new_mmap(self.temp_mrc_name,
                              (3, 4, 5),
                              mrc_mode=2,
                              fill=1.1,
                              extended_header=np.zeros(1, dtype=np.int8),
                              exttyp='TYPE') as mrc:
            assert repr(mrc) == ("MrcMemmap('{0}', mode='w+')"
                                 .format(self.temp_mrc_name))
            assert mrc.data.shape == (3, 4, 5)
            assert np.all(mrc.data == 1.1)
            assert mrc.header.nx == 5
            assert mrc.header.nsymbt == 1
            assert mrc.extended_header.nbytes == 1
            assert mrc.header.exttyp == b'TYPE'
            mrc._iostream.seek(0, os.SEEK_END)
            file_size = mrc._iostream.tell()
            exp_size = mrc.header.nbytes + mrc.extended_header.nbytes + mrc.data.nbytes
            assert file_size == exp_size

    def test_new_mmap_with_aligned_offset(self):
        # Test for awkward situation in https://github.com/ccpem/mrcfile/issues/65
        # A zero-size mmap is created during the process of creating a new MrcMemmap
        # object. If the header size is an exact multiple of mmap.ALLOCATIONGRANULARITY,
        # mmap creation fails with an error.
        problem_ext_head_size = mmap.ALLOCATIONGRANULARITY - 1024
        with mrcfile.new_mmap(self.temp_mrc_name,
                              (3, 4, 5),
                              mrc_mode=2,
                              fill=1.1,
                              extended_header=np.zeros(problem_ext_head_size,
                                                       dtype=np.int8)) as mrc:
            assert repr(mrc) == ("MrcMemmap('{0}', mode='w+')"
                                 .format(self.temp_mrc_name))
            assert mrc.data.shape == (3, 4, 5)
            assert np.all(mrc.data == 1.1)
            assert mrc.header.nx == 5
            assert mrc.header.nsymbt == problem_ext_head_size
            assert mrc.extended_header.nbytes == problem_ext_head_size

            # The workaround for this bug adds one extra byte to the file to avoid
            # triggering the mmap error. After a data array has been set, the file size
            # should be normal again.
            mrc._iostream.seek(0, os.SEEK_END)
            file_size = mrc._iostream.tell()
            exp_size = mrc.header.nbytes + mrc.extended_header.nbytes + mrc.data.nbytes
            assert file_size == exp_size

    @unittest.skipIf(sys.maxsize <= np.iinfo(np.int32).max, "can't run test on 32-bit")
    def test_new_mmap_with_extended_header_too_big(self):
        ext = np.empty((int(np.iinfo(np.int32).max) + 1,), dtype='V1')
        with self.assertRaisesRegex(ValueError, "extended header is too large"):
            mrcfile.new_mmap(self.temp_mrc_name,
                             (3, 4, 5, 6),
                             mrc_mode=2,
                             fill=1.1,
                             extended_header=ext)

    def test_new_mmap_with_shape_too_big(self):
        with self.assertRaisesRegex(ValueError, "shape is too large"):
            mrcfile.new_mmap(self.temp_mrc_name,
                             (np.iinfo(np.int32).max + 1, 1))

    def test_write(self):
        data_in = np.random.random((10, 10)).astype(np.float16)
        mrcfile.write(self.temp_mrc_name, data_in, voxel_size=1.1)
        with mrcfile.open(self.temp_mrc_name) as mrc:
            data_out = mrc.data
            voxel_size = mrc.voxel_size
        assert np.allclose(data_in, data_out)
        self.assertAlmostEqual(voxel_size.x, 1.1)
        self.assertAlmostEqual(voxel_size.y, 1.1)
        self.assertAlmostEqual(voxel_size.z, 1.1)

    def test_write_with_auto_compression(self):
        data_in = np.random.random((10, 10)).astype(np.float16)
        mrcfile.write(self.temp_gz_mrc_name, data_in)
        with mrcfile.open(self.temp_gz_mrc_name) as mrc:
            assert isinstance(mrc, GzipMrcFile)


@unittest.skipIf(pathlib_unavailable, "pathlib not available")
class LoadFunctionTestWithPathlib(LoadFunctionTest):

    """Class to run the load function tests using pathlib paths instead of strings."""

    def setUp(self):
        super(LoadFunctionTestWithPathlib, self).setUp()
        self.temp_mrc_name = Path(self.temp_mrc_name)
        self.temp_gz_mrc_name = Path(self.temp_gz_mrc_name)
        self.example_mrc_name = Path(self.example_mrc_name)
        self.gzip_mrc_name = Path(self.gzip_mrc_name)
        self.bzip2_mrc_name = Path(self.bzip2_mrc_name)
        self.slow_mrc_name = Path(self.slow_mrc_name)


if __name__ == '__main__':
    unittest.main()
