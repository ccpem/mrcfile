# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
mrcfile
-------

A pure Python implementation of the MRC2014 file format.

The MRC2014 format was described in the Journal of Structural Biology:
http://dx.doi.org/10.1016/j.jsb.2015.04.002

The format specification is available on the CCP-EM website:
http://www.ccpem.ac.uk/mrc_format/mrc2014.php

TODO: usage examples

"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from .mrcfile import MrcFile

__version__ = '0.0.1'


def new(name, data=None, mrcmode=None, shape=None, overwrite=False):
    """Create a new MRC file."""
    mrc = MrcFile(name, mode='w+', overwrite=overwrite)
    if data is not None:
        mrc.set_data(data)
    return mrc


def read(name, mode='r'):
    # TODO: make this do something!
    pass
