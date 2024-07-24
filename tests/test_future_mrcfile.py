# Copyright (c) 2018, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for future_mrcfile.py.
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time
import unittest

from mrcfile.future_mrcfile import FutureMrcFile
from . import helpers


def sleep_and_return_args(*args, **kwargs):
    """Simple test function to wait a short time and return its arguments."""
    time.sleep(0.01)
    return [args, kwargs]


class FutureMrcFileTest(helpers.AssertRaisesRegexMixin, unittest.TestCase):

    """Unit tests for FutureMrcFile.

    These tests only make sure that the FutureMrcFile class works correctly
    in terms of function calling and behaviour. Actual testing of asynchronous
    MRC file opening is done in test_load_functions.py.

    """

    def setUp(self):
        self.future_mrc_file = FutureMrcFile(sleep_and_return_args)

    def tearDown(self):
        pass

    def test_cancel(self):
        assert self.future_mrc_file.cancel() == False

    def test_cancelled(self):
        assert self.future_mrc_file.cancelled() == False

    def test_add_done_callback(self):
        with self.assertRaises(NotImplementedError):
            self.future_mrc_file.add_done_callback(sleep_and_return_args)

    def test_running_and_done_status(self):
        assert self.future_mrc_file.running() == True
        assert self.future_mrc_file.done() == False
        self.future_mrc_file.result()
        assert self.future_mrc_file.running() == False
        assert self.future_mrc_file.done() == True

    def test_arguments_passed_correctly(self):
        args = (1, 2, 'a')
        kwargs = {'a': 'b', 'c': 3}
        future_mrc_file = FutureMrcFile(sleep_and_return_args, args, kwargs)
        result = future_mrc_file.result()
        assert result[0] == args
        assert result[1] == kwargs

        # Also check the results from the Future from setUp()
        result_no_args = self.future_mrc_file.result()
        assert result_no_args[0] == ()
        assert result_no_args[1] == {}

    def test_timeout_from_result(self):
        with self.assertRaisesRegex(RuntimeError, "Timed out"):
            FutureMrcFile(sleep_and_return_args).result(0.001)

    def test_timeout_from_exception(self):
        with self.assertRaisesRegex(RuntimeError, "Timed out"):
            FutureMrcFile(sleep_and_return_args).exception(0.001)

    def test_exception(self):
        future_mrc_file = FutureMrcFile(lambda: 1/0)
        ex = future_mrc_file.exception()
        assert isinstance(ex, ZeroDivisionError)
        with self.assertRaises(ZeroDivisionError) as cm:
            future_mrc_file.result()
            assert cm.exception == ex
