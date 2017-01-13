mrcfile.py
==========

|build-status| |pypi-version| |python-versions| |readthedocs|

.. |build-status| image:: https://travis-ci.org/ccpem/mrcfile.svg?branch=master
    :target: https://travis-ci.org/ccpem/mrcfile
    :alt: Build Status

.. |pypi-version| image:: https://img.shields.io/pypi/v/mrcfile.svg
    :target: https://pypi.python.org/pypi/mrcfile
    :alt: Python Package Index
    
.. |python-versions| image:: https://img.shields.io/pypi/pyversions/mrcfile.svg
    :target: https://pypi.python.org/pypi/mrcfile
    :alt: Python Versions

.. |readthedocs| image:: https://readthedocs.org/projects/mrcfile/badge/
    :target: http://mrcfile.readthedocs.org
    :alt: Documentation

.. start_of_main_text

mrcfile.py is a Python implementation of the `MRC2014 file format`_, which is
used to store image and volume data in the field of structural biology.

It allows MRC files to be created and opened easily using a very simple API,
which exposes the file's header and data as `numpy`_ arrays. The code runs in
Python 2 and 3 and is fully unit-tested.

.. _MRC2014 file format: MRC2014_
.. _MRC2014: http://www.ccpem.ac.uk/mrc_format/mrc2014.php
.. _numpy: http://www.numpy.org/

The intent of this library is to allow users and developers to read and write
standard-compliant MRC files in Python as easily as possible, and with no
dependencies on any compiled libraries except `numpy`_. You can use it
interactively to inspect files, correct headers and so on, or in scripts and
larger software packages to provide basic MRC file I/O functions.

Key Features
------------

* Clean, simple API for access to MRC files
* Easy to install and use
* Seamless support for gzip files
* Memory-mapped file option for fast random access to very large files
* Runs in Python 2 & 3

Installation
------------

The ``mrcfile`` library is available from the Python package index::

    pip install mrcfile

The source code (including the full test suite) can be found on GitHub:
https://github.com/ccpem/mrcfile

Basic usage
-----------

The easiest way to open a file is with the `mrcfile.open`_ and `mrcfile.new`_
functions. These return an `MrcFile`_ object which represents an MRC file on
disk.

.. _mrcfile.open: http://mrcfile.readthedocs.io/en/latest/source/mrcfile.html#mrcfile.open
.. _mrcfile.new: http://mrcfile.readthedocs.io/en/latest/source/mrcfile.html#mrcfile.new
.. _MrcFile: http://mrcfile.readthedocs.io/en/latest/mrcfile_api_overview.html

To open an MRC file and read a slice of data::

    >>> import mrcfile
    >>> with mrcfile.open('tests/test_data/EMD-3197.map') as mrc:
    >>>     mrc.data[10,10]
    array([ 2.58179283,  3.1406002 ,  3.64495397,  3.63812137,  3.61837363,
            4.0115056 ,  3.66981959,  2.07317996,  0.1251585 , -0.87975615,
            0.12517013,  2.07319379,  3.66982722,  4.0115037 ,  3.61837196,
            3.6381247 ,  3.64495087,  3.14059472,  2.58178973,  1.92690361], dtype=float32)

To create a new file with a 2D data array, and change some values::

    >>> with mrcfile.new('tmp.mrc') as mrc:
    >>>     mrc.set_data(np.zeros((5, 5), dtype=np.int8))
    >>>     mrc.data
    array([[0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0]], dtype=int8)
    >>>     mrc.data[1:4,1:4] = 10
    >>>     mrc.data
    array([[ 0,  0,  0,  0,  0],
           [ 0, 10, 10, 10,  0],
           [ 0, 10, 10, 10,  0],
           [ 0, 10, 10, 10,  0],
           [ 0,  0,  0,  0,  0]], dtype=int8)

Close the file after use by calling ``close()`` which will save the data to disk
when the file is closed. You can also call ``flush()`` manually to flush the
data to disk and keep the file open. If you open a file using Python's ``with``
keyword (as in the examples above), it will be closed automatically at the end
of the ``with`` block, like a normal Python file object.

Documentation
-------------

Full documentation is available at http://mrcfile.readthedocs.org

Contributing
------------

Issues: https://github.com/ccpem/mrcfile/issues

Code contributions are also welcome, please submit pull requests to the GitHub
repository.

Licence
-------

The project is released under the BSD licence.

