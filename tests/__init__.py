# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""Tests for the mrcfile package."""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import unittest

from .test_utils import UtilsTest
from .test_mrcobject import MrcObjectTest
from .test_mrcinterpreter import MrcInterpreterTest
from .test_mrcfile import MrcFileTest
from .test_gzipmrcfile import GzipMrcFileTest
from .test_mrcmemmap import MrcMemmapTest

test_classes = [
    UtilsTest,
    MrcObjectTest,
    MrcInterpreterTest,
    MrcFileTest,
    GzipMrcFileTest,
    MrcMemmapTest
]

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_classes:
        suite.addTest(loader.loadTestsFromTestCase(test_class))
    return suite
