# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Module to provide helper utilities for mrcfile tests.
"""

import os


def get_test_data_path():
    """Get the path to the test data directory.

    This function needs to be in a separate module to ensure that the __file__
    constant exists.
    """
    return os.path.join(os.path.dirname(__file__), "test_data")
