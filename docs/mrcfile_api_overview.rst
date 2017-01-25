mrcfile.py API overview
=======================

.. testsetup:: *

   import os
   import shutil
   import tempfile
   
   import numpy as np
   import mrcfile
   
   old_cwd = os.getcwd()
   tempdir = tempfile.mkdtemp()
   os.chdir(tempdir)

.. testcleanup:: *

   os.chdir(old_cwd)
   shutil.rmtree(tempdir)

Using MrcFile objects
---------------------

Opening and closing
~~~~~~~~~~~~~~~~~~~

MRC files should usually be opened using the :func:`mrcfile.new` or
:func:`mrcfile.open` functions. These return an instance of the
:class:`~mrcfile.mrcfile.MrcFile` class, which represents an MRC file on disk
and makes the file's header, extended header and data available for read and
write access as ``numpy`` arrays:

.. doctest::

   >>> # First, create a simple dataset
   >>> import numpy as np
   >>> example_data = np.arange(12, dtype=np.int8).reshape(3, 4)

   >>> # Make a new MRC file and write the data to it:
   >>> import mrcfile
   >>> with mrcfile.new('tmp.mrc') as mrc:
   ...     mrc.set_data(example_data)
   ... 
   >>> # The file is now saved on disk. Open it again and check the data:
   >>> with mrcfile.open('tmp.mrc') as mrc:
   ...     mrc.data
   array([[ 0,  1,  2,  3],
          [ 4,  5,  6,  7],
          [ 8,  9, 10, 11]], dtype=int8)

The :func:`~mrcfile.new` and :func:`~mrcfile.open` functions can also handle
gzipped files very easily:

.. doctest::

   >>> # Make a new gzipped MRC file:
   >>> with mrcfile.new('tmp.mrc.gz', gzip=True) as mrc:
   ...     mrc.set_data(example_data * 2)
   ... 
   >>> # Open it again with the normal open function:
   >>> with mrcfile.open('tmp.mrc.gz') as mrc:
   ...     mrc.data
   array([[ 0,  2,  4,  6],
          [ 8, 10, 12, 14],
          [16, 18, 20, 22]], dtype=int8)

:class:`~mrcfile.mrcfile.MrcFile` objects should be closed when they are
finished with, to ensure any changes are flushed to disk and the underlying file
object is closed:

.. doctest::

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')
   >>> # do things...
   >>> mrc.close()

As we saw in the examples above, :class:`~mrcfile.mrcfile.MrcFile` objects
support Python's ``with`` statement, which will ensure the file is closed
properly after use (like a normal Python file object). It's generally a good
idea to use ``with`` if possible, but sometimes when running Python
interactively (as in some of these examples), it's more convenient to open a
file and keep using it without having to work in an indented block. If you do
this, remember to close the file at the end!

There's also a :meth:`~mrcfile.mrcinterpreter.MrcInterpreter.flush` method that
writes the MRC data to disk but leaves the file open:

.. doctest::

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')
   >>> # do things...
   >>> mrc.flush()  # make sure changes are written to disk
   >>> # continue using the file...
   >>> mrc.close()  # close the file when finished

With very large files, it might be helpful to use the :func:`mrcfile.mmap`
function to open the file, which will open the data as a memory-mapped ``numpy``
array. The contents of the array are only read from disk as needed, so this
allows large files to be opened quickly. Parts of the data can then be read and
written by slicing the array:

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> # Open the file in memory-mapped mode
   >>> mrc = mrcfile.mmap('tmp.mrc', mode='r+')
   >>> # Now read part of the data by slicing
   >>> mrc.data[1:3]
   memmap([[ 4,  5,  6,  7],
           [ 8,  9, 10, 11]], dtype=int8)

   >>> # Set some values by assigning to a slice
   >>> mrc.data[:,1:3] = 0

   >>> # Read the entire array - with large files this might take a while!
   >>> mrc.data[:]
   memmap([[ 0,  0,  0,  3],
           [ 4,  0,  0,  7],
           [ 8,  0,  0, 11]], dtype=int8)
   >>> mrc.close()

For most purposes, the top-level functions in :mod:`mrcfile` should be all you
need to open MRC files, but it is also possible to directly instantiate
:class:`~mrcfile.mrcfile.MrcFile` and its subclasses,
:class:`~mrcfile.gzipmrcfile.GzipMrcFile` and
:class:`~mrcfile.mrcmemmap.MrcMemmap`:

.. doctest::

   >>> with mrcfile.MrcFile('tmp.mrc') as mrc:
   ...     mrc
   MrcFile('tmp.mrc', mode='r')

   >>> with mrcfile.GzipMrcFile('tmp.mrc.gz') as mrc:
   ...     mrc
   GzipMrcFile('tmp.mrc.gz', mode='r')

   >>> with mrcfile.MrcMemmap('tmp.mrc') as mrc:
   ...     mrc
   MrcMemmap('tmp.mrc', mode='r')

File modes
~~~~~~~~~~

:class:`~mrcfile.mrcfile.MrcFile` objects can be opened in three modes: ``r``,
``r+`` and ``w+``. These correspond to the standard Python file modes, so ``r``
opens a file in read-only mode:

.. doctest::

   >>> # The default mode is 'r', for read-only access:
   >>> mrc = mrcfile.open('tmp.mrc')
   >>> mrc
   MrcFile('tmp.mrc', mode='r')
   >>> mrc.set_data(example_data)
   Traceback (most recent call last):
   ...
   ValueError: MRC object is read-only
   >>> mrc.close()

``r+`` opens it for reading and writing:

.. doctest::

   >>> # Using mode 'r+' allows read and write access:
   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')
   >>> mrc
   MrcFile('tmp.mrc', mode='r+')
   >>> mrc.set_data(example_data)
   >>> mrc.data
   array([[ 0,  1,  2,  3],
          [ 4,  5,  6,  7],
          [ 8,  9, 10, 11]], dtype=int8)
   >>> mrc.close()

and ``w+`` opens a new, empty file (also for both reading and writing):

.. doctest::

   >>> # Mode 'w+' creates a new empty file:
   >>> mrc = mrcfile.open('empty.mrc', mode='w+')
   >>> mrc
   MrcFile('empty.mrc', mode='w+')
   >>> mrc.data
   array([], dtype=int8)
   >>> mrc.close()

The :func:`~mrcfile.new` function is effectively shorthand for
``open(name, mode='w+')``:

.. doctest::

   >>> # Make a new file
   >>> mrc = mrcfile.new('empty.mrc')
   Traceback (most recent call last):
   ...
   IOError: File 'empty.mrc' already exists; set overwrite=True to overwrite it
   >>> # Ooops, we've already got a file with that name!
   >>> # If we're sure we want to overwrite it, we can try again:
   >>> mrc = mrcfile.new('empty.mrc', overwrite=True)
   >>> mrc
   MrcFile('empty.mrc', mode='w+')
   >>> mrc.close()

Accessing the header and data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The header and data arrays can be accessed using the
:attr:`~mrcfile.mrcobject.MrcObject.header`,
:attr:`~mrcfile.mrcobject.MrcObject.extended_header` and 
:attr:`~mrcfile.mrcobject.MrcObject.data` attributes. These attributes are
read-only and cannot be assigned to directly, but (unless the file mode is 'r')
the arrays can be modified in-place. The extended header and data arrays can
also be completely replaced by calling the
:meth:`~mrcfile.mrcobject.MrcObject.set_extended_header` and
:meth:`~mrcfile.mrcobject.MrcObject.set_data` methods.

The header is a numpy `record array`_, meaning that fields can be accessed as
normal attributes, for example ``mrc.header.nx`` for the number of columns in
the map.

.. _record array: https://docs.scipy.org/doc/numpy/user/basics.rec.html#record-arrays

For a quick overview of the contents of a file's header, call
:meth:`~mrcfile.mrcobject.MrcObject.print_header`.

Voxel size
~~~~~~~~~~

The voxel (or pixel) size in the file can be accessed using the
:attr:`~mrcfile.mrcobject.MrcObject.voxel_size` attribute, which returns a numpy
record array with three fields, ``x``, ``y`` and ``z``, for the voxel size in
each dimension. (The sizes are not stored directly in the MRC header, but are
calculated when required from the header's cell and grid size fields.) You can
also set the voxel size by assigning to the
:attr:`~mrcfile.mrcobject.MrcObject.voxel_size` attribute, using a single number
(for an isotropic voxel size), a 3-tuple or a single-item record array with
``x``, ``y`` and ``z`` fields. This will set a new cell size in the MRC header
so that the grid spacing matches the given values.

Keeping the header and data in sync
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a new data array is given (using
:meth:`~mrcfile.mrcobject.MrcObject.set_data` or the ``data`` argument to
:func:`~mrcfile.new`), the header is automatically updated to ensure the file
is valid. If the data array is modified in place, for example by editing values
or changing the shape or dtype attributes, the header will no longer be correct.
To keep the header in sync with the data, three methods can be used to update
the header:

* :meth:`~mrcfile.mrcobject.MrcObject.update_header_from_data`: This updates the
  header's dimension fields, mode, space group and machine stamp to be
  consistent with the data array. Because it only inspects the data array's
  attributes, this method is fast even for very large arrays.

* :meth:`~mrcfile.mrcobject.MrcObject.update_header_stats`: This updates the
  data statistics fields in the header (dmin, dmax, dmean and rms). This method
  can be slow with large data arrays because it has to access the full contents
  of the array.

* :meth:`~mrcfile.mrcobject.MrcObject.reset_header_stats`: If the data values
  have changed and the statistics fields are invalid, but the data array is very
  large and you do not want to wait for ``update_header_stats()`` to run, you
  can call this method to reset the header's statistics fields to indicate that
  the values are undetermined.

Data dimensionality
~~~~~~~~~~~~~~~~~~~

MRC files can be used to store several types of data: single images, image
stacks, volumes and volume stacks. If you set a new data array in an MrcFile
object (using :meth:`~mrcfile.mrcobject.MrcObject.set_data` or the ``data``
argument to :func:`~mrcfile.new`), it will be treated as follows:

* 2D data array: single image, space group 0.
* 3D data array: volume, space group 1, unless the file already contains an
  image stack in which case new 3D data continues to be treated as an image
  stack.
* 4D data array: volume stack, space group 401.

Any other number of data dimensions will raise an exception.

The dimensionality of an existing MrcFile can be identified by checking the data
array's shape and the ``ispg`` field in the header, or more conveniently using
the :meth:`~mrcfile.mrcobject.MrcObject.is_single_image`,
:meth:`~mrcfile.mrcobject.MrcObject.is_image_stack`,
:meth:`~mrcfile.mrcobject.MrcObject.is_volume` and
:meth:`~mrcfile.mrcobject.MrcObject.is_volume_stack` methods. For 3D data, the
intepretation can be switched by calling
:meth:`~mrcfile.mrcobject.MrcObject.set_image_stack` and
:meth:`~mrcfile.mrcobject.MrcObject.set_volume`.

Note that the MRC format allows the data axes to be swapped using the header's
``mapc``, ``mapr`` and ``maps`` fields. This library does not attempt to swap
the axes and simply assigns the columns to X, rows to Y and sections to Z. (The
data array is indexed in C style, so data values can be accessed using
``mrc.data[z][y][x]``.)

Data types
~~~~~~~~~~

Various numpy `data types`_ can be used for MRC data arrays. The conversions to
MRC mode numbers are given in the documentation for
:func:`~mrcfile.utils.mode_from_dtype`. The important point to note is that
some types cannot be used in MRC files, including integer types of more than 16
bits, or float types of more than 32 bits. Many numpy array creation routines
use int64 or float64 dtypes by default, which means you will need to give a
dtype argument to ensure the array can be used in an MRC file:

.. _data types: https://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html

.. doctest::

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')
   >>> # This does not work
   >>> mrc.set_data(np.zeros((3, 10)))
   Traceback (most recent call last):
   ...
   ValueError: dtype 'float64' cannot be converted to an MRC file mode
   >>> # But this does
   >>> mrc.set_data(np.zeros((3, 10), dtype=np.int16))
   >>> mrc.data
   array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], dtype=int16)
   >>> mrc.close()

Class hierarchy
---------------

The following classes are provided by the mrcfile.py library:

* :class:`~mrcfile.mrcobject.MrcObject`: Represents a generic MRC-like data
  object in memory, and provides header, extended header and data arrays and
  methods for operating on them.

* :class:`~mrcfile.mrcinterpreter.MrcInterpreter`: Subclass of MrcObject that
  can read and/or write its MRC data from arbitrary byte I/O streams
  (including Python file objects).

* :class:`~mrcfile.mrcfile.MrcFile`: Subclass of MrcInterpreter that opens a
  file from disk to use as its I/O stream. This is the normal class used for
  most interactions with MRC files.

* :class:`~mrcfile.gzipmrcfile.GzipMrcFile`: Reads and writes MRC data using
  compressed gzip files.

* :class:`~mrcfile.mrcmemmap.MrcMemmap`: Uses a memory-mapped data array, for
  fast random access to very large data files. MrcMemmap overrides various
  parts of the MrcFile implementation to ensure that the memory-mapped data
  array is opened, closed and moved correctly when the data or extended header
  array sizes are changed.

MrcFile attributes and methods
------------------------------

Attributes:

* :attr:`~mrcfile.mrcobject.MrcObject.header`
* :attr:`~mrcfile.mrcobject.MrcObject.extended_header`
* :attr:`~mrcfile.mrcobject.MrcObject.data`
* :attr:`~mrcfile.mrcobject.MrcObject.voxel_size`

Methods:

* :meth:`~mrcfile.mrcobject.MrcObject.set_extended_header`
* :meth:`~mrcfile.mrcobject.MrcObject.set_data`
* :meth:`~mrcfile.mrcobject.MrcObject.is_single_image`
* :meth:`~mrcfile.mrcobject.MrcObject.is_image_stack`
* :meth:`~mrcfile.mrcobject.MrcObject.is_volume`
* :meth:`~mrcfile.mrcobject.MrcObject.is_volume_stack`
* :meth:`~mrcfile.mrcobject.MrcObject.set_image_stack`
* :meth:`~mrcfile.mrcobject.MrcObject.set_volume`
* :meth:`~mrcfile.mrcobject.MrcObject.update_header_from_data`
* :meth:`~mrcfile.mrcobject.MrcObject.update_header_stats`
* :meth:`~mrcfile.mrcobject.MrcObject.reset_header_stats`
* :meth:`~mrcfile.mrcobject.MrcObject.print_header`
* :meth:`~mrcfile.mrcinterpreter.MrcInterpreter.flush`
* :meth:`~mrcfile.mrcinterpreter.MrcInterpreter.close`
