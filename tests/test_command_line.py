# Copyright (c) 2018, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for mrcfile command line entry point functions.
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io
import os
import shutil
import sys
import tempfile
import unittest

from mrcfile import command_line
from . import helpers


class CommandLineTest(helpers.AssertRaisesRegexMixin, unittest.TestCase):
    
    """Unit tests for mrcfile command line functions.
    
    """
    
    def setUp(self):
        super(CommandLineTest, self).setUp()
        
        # Set up test files and names to be used
        self.test_data = helpers.get_test_data_path()
        self.test_output = tempfile.mkdtemp()
        
        self.files = [
            os.path.join(self.test_data, 'EMD-3197.map'),
            os.path.join(self.test_data, 'emd_3001.map.gz'),
            os.path.join(self.test_data, 'EMD-3197.map.bz2')
        ]
        
        # Set up stream to catch print output from print_header()
        self.print_stream = io.StringIO()
        
        # Replace stdout and stderr to capture output for checking
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
    
    def tearDown(self):
        # Restore stdout and stderr
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr
        
        if os.path.exists(self.test_output):
            shutil.rmtree(self.test_output)
        super(CommandLineTest, self).tearDown()
    
    def test_print_header_one_file(self):
        command_line.print_headers(self.files, print_file=self.print_stream)
        printed = self.print_stream.getvalue()
        assert len(printed) > 0
        assert "nx" in printed
        assert "machst          : [68 65  0  0]" in printed
        assert "::::EMDATABANK.org::::EMD-3197::::" in printed
        assert len(sys.stdout.getvalue()) == 0
        assert len(sys.stderr.getvalue()) == 0


if __name__ == '__main__':
    unittest.main()
