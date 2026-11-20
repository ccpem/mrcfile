# Copyright (c) 2022, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for dtypes.py
"""

import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

import mrcfile
from mrcfile import dtypes, utils


class DtypesTest(unittest.TestCase):
    """Unit tests for mrcfile.dtypes"""

    def test_invalid_byte_order_raises_exception(self):
        with self.assertRaisesRegex(ValueError, "Unrecognised byte order indicator"):
            _ = dtypes.get_ext_header_dtype(b"", "a")

    def test_fei1_ext_header_with_native_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b"FEI1")
        assert dtype.itemsize == 768
        assert utils.byte_orders_equal(dtype["Metadata size"].byteorder, "=")
        with self.assertRaises(KeyError):
            _ = dtype["Scan rotation"]
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype["Bitmask 1"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 2"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 3"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 4"].byteorder, "<")

    def test_fei2_ext_header_with_native_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b"FEI2")
        assert dtype.itemsize == 888
        assert utils.byte_orders_equal(dtype["Metadata size"].byteorder, "=")
        assert dtype["Scan rotation"] is not None
        assert utils.byte_orders_equal(dtype["Scan rotation"].byteorder, "=")
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype["Bitmask 1"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 2"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 3"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 4"].byteorder, "<")

    def test_fei1_ext_header_with_little_endian_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b"FEI1", "<")
        # Normal fields should match the requested byte order
        assert utils.byte_orders_equal(dtype["Metadata size"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Alpha tilt"].byteorder, "<")
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype["Bitmask 1"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 2"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 3"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 4"].byteorder, "<")

    def test_fei2_ext_header_with_little_endian_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b"FEI2", "<")
        # Normal fields should match the requested byte order
        assert utils.byte_orders_equal(dtype["Metadata size"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Alpha tilt"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Scan rotation"].byteorder, "<")
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype["Bitmask 1"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 2"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 3"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 4"].byteorder, "<")

    def test_fei1_ext_header_with_big_endian_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b"FEI1", ">")
        # Normal fields should match the requested byte order
        assert utils.byte_orders_equal(dtype["Metadata size"].byteorder, ">")
        assert utils.byte_orders_equal(dtype["Alpha tilt"].byteorder, ">")
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype["Bitmask 1"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 2"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 3"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 4"].byteorder, "<")

    def test_fei2_ext_header_with_big_endian_byte_order(self):
        dtype = dtypes.get_ext_header_dtype(b"FEI2", ">")
        # Normal fields should match the requested byte order
        assert utils.byte_orders_equal(dtype["Metadata size"].byteorder, ">")
        assert utils.byte_orders_equal(dtype["Alpha tilt"].byteorder, ">")
        assert utils.byte_orders_equal(dtype["Scan rotation"].byteorder, ">")
        # Bitmasks should always be little-endian
        assert utils.byte_orders_equal(dtype["Bitmask 1"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 2"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 3"].byteorder, "<")
        assert utils.byte_orders_equal(dtype["Bitmask 4"].byteorder, "<")

    def test_new_ext_header_initialises_each_record(self):
        formats = [(b"FEI1", 768, 0), (b"FEI2", 888, 2)]
        for exttyp, size, version in formats:
            for byte_order in ("<", ">", "="):
                with self.subTest(exttyp=exttyp, byte_order=byte_order):
                    header = dtypes.new_ext_header(exttyp, 3, byte_order=byte_order)
                    assert header.shape == (3,)
                    assert header.dtype == dtypes.get_ext_header_dtype(
                        exttyp, byte_order
                    )
                    endian = utils.normalise_byte_order(byte_order)
                    expected_prefix = struct.pack(f"{endian}ii", size, version)
                    expected_record = expected_prefix + bytes(
                        size - len(expected_prefix)
                    )
                    assert header.tobytes() == expected_record * 3

    def test_new_ext_header_round_trip(self):
        for exttyp in (b"FEI1", b"FEI2"):
            for writer, byte_order in (("new", "<"), ("new", ">"), ("new_mmap", "=")):
                with (
                    self.subTest(exttyp=exttyp, writer=writer, byte_order=byte_order),
                    tempfile.TemporaryDirectory() as temp_dir,
                ):
                    path = Path(temp_dir) / "image_stack.mrc"
                    data = np.arange(24).astype(f"{byte_order}f4").reshape(3, 2, 4)
                    header = dtypes.new_ext_header(
                        exttyp, data.shape[0], byte_order=byte_order
                    )
                    header["Alpha tilt"] = [-20.0, 0.0, 20.0]
                    header["Bitmask 1"] = 1 << 7
                    if writer == "new_mmap":
                        with mrcfile.new_mmap(
                            path,
                            data.shape,
                            mrc_mode=2,
                            extended_header=header,
                            exttyp=exttyp,
                        ) as mrc:
                            mrc.data[...] = data
                            mrc.update_header_stats()
                    else:
                        with mrcfile.new(path) as mrc:
                            mrc.set_data(data)
                            mrc.set_extended_header(header)
                            mrc.header.exttyp = exttyp
                    with mrcfile.open(path) as mrc:
                        assert mrc.header.exttyp == exttyp
                        assert mrc.header.nsymbt == header.nbytes
                        indexed = mrc.indexed_extended_header
                        np.testing.assert_array_equal(indexed, header)
                        np.testing.assert_array_equal(mrc.data, data)

    def test_new_ext_header_allows_no_records(self):
        header = dtypes.new_ext_header(b"FEI1", 0)
        assert header.shape == (0,)
        assert header.dtype == dtypes.get_ext_header_dtype(b"FEI1")

    def test_new_ext_header_rejects_invalid_record_count(self):
        for count in (-1, 2**31 // 768 + 1):
            with (
                self.subTest(count=count),
                self.assertRaisesRegex(ValueError, "record count"),
            ):
                dtypes.new_ext_header(b"FEI1", count)

    def test_new_ext_header_rejects_unknown_type_and_byte_order(self):
        with self.assertRaisesRegex(ValueError, "extended header type"):
            dtypes.new_ext_header(b"SERI", 1)
        with self.assertRaisesRegex(ValueError, "Unrecognised byte order indicator"):
            dtypes.new_ext_header(b"FEI2", 1, byte_order="a")


if __name__ == "__main__":
    unittest.main()
