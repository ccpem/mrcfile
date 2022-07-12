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

from mrcfile import command_line, validator
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

    def test_print_header_no_args(self):
        command_line.print_headers([], print_file=self.print_stream)
        assert len(self.print_stream.getvalue()) == 0
        assert len(sys.stdout.getvalue()) == 0
        assert len(sys.stderr.getvalue()) == 0

    def test_print_header_nonexistent_file(self):
        with self.assertRaisesRegex(IOError, "No such file"):
            command_line.print_headers(["nonexistent.mrc"],
                                       print_file=self.print_stream)
        assert len(self.print_stream.getvalue()) == 0
        assert len(sys.stdout.getvalue()) == 0
        assert len(sys.stderr.getvalue()) == 0

    def test_print_header(self):
        command_line.print_headers(self.files, print_file=self.print_stream)
        printed = self.print_stream.getvalue()
        assert len(printed) > 0
        for file in self.files:
            assert "MRC header for " + file in printed
        assert "nx" in printed
        assert "machst          : [68 65  0  0]" in printed
        assert "::::EMDATABANK.org::::EMD-3197::::" in printed
        assert len(sys.stdout.getvalue()) == 0
        assert len(sys.stderr.getvalue()) == 0

    def test_validate_no_args(self):
        result = validator.main([])
        assert result == 0
        assert len(self.print_stream.getvalue()) == 0
        assert len(sys.stdout.getvalue()) == 0
        assert len(sys.stderr.getvalue()) == 0
    
    def test_validate(self):
        result = validator.main(self.files)
        assert result == 1
        stdout = str(sys.stdout.getvalue())
        assert stdout == (
            "Checking if " + self.files[0] + " is a valid MRC2014 file...\n"
            "File does not declare MRC format version 20140 or 20141: nversion = 0\n"
            "Checking if " + self.files[1] + " is a valid MRC2014 file...\n"
            "File does not declare MRC format version 20140 or 20141: nversion = 0\n"
            "Extended header type is undefined or unrecognised: exttyp = ''\n"
            "Checking if " + self.files[2] + " is a valid MRC2014 file...\n"
            "File does not declare MRC format version 20140 or 20141: nversion = 0\n"
        )
        assert len(sys.stderr.getvalue()) == 0


if __name__ == '__main__':
    unittest.main()
