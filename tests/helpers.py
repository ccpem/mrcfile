# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Module to provide helper utilities for mrcfile tests.
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import unittest


def get_test_data_path():
    """ Get the path to the test data directory.
    
    This function needs to be in a separate module to ensure that the __file__
    constant exists.
    """
    return os.path.join(os.path.dirname(__file__), 'test_data')


class AssertRaisesRegexMixin(object):
    
    """Mixin to ensure test cases can call assertRaisesRegex in Python 2 and 3.
    
    """
    
    def assertRaisesRegex(self, *args, **kwargs):
        """Simple wrapper to avoid deprecation warnings from assertRaisesRegexp
        on Python 3."""
        if hasattr(unittest.TestCase, "assertRaisesRegex"):
            return unittest.TestCase.assertRaisesRegex(self, *args, **kwargs)  # @UndefinedVariable
        else:
            return unittest.TestCase.assertRaisesRegexp(self, *args, **kwargs)
