# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""Tests for the mrcfile package."""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import unittest

from .test_bzip2mrcfile import Bzip2MrcFileTest
from .test_command_line import CommandLineTest
from .test_dtypes import DtypesTest
from .test_future_mrcfile import FutureMrcFileTest
from .test_gzipmrcfile import GzipMrcFileTest
from .test_load_functions import LoadFunctionTest, LoadFunctionTestWithPathlib
from .test_mrcfile import MrcFileTest
from .test_mrcinterpreter import MrcInterpreterTest
from .test_mrcmemmap import MrcMemmapTest
from .test_mrcobject import MrcObjectTest
from .test_utils import UtilsTest
from .test_validation import ValidationTest

test_classes = [
    Bzip2MrcFileTest,
    CommandLineTest,
    DtypesTest,
    FutureMrcFileTest,
    GzipMrcFileTest,
    LoadFunctionTest,
    LoadFunctionTestWithPathlib,
    MrcFileTest,
    MrcInterpreterTest,
    MrcObjectTest,
    MrcMemmapTest,
    UtilsTest,
    ValidationTest
]

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_classes:
        suite.addTest(loader.loadTestsFromTestCase(test_class))
    return suite
