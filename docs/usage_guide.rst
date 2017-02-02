Usage Guide
===========

Beta version warning!
---------------------

Please note: this library is currently in beta: the API and usage
instructions could still change before the first stable release.

If you have any feedback or suggestions for improvement (about the API, design,
usability, documentation or anything else), please raise issues on the
`GitHub issue tracker`_ or email colin.palmer@stfc.ac.uk.

.. _GitHub issue tracker: https://github.com/ccpem/mrcfile/issues

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
   ... 
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
   ... 
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

Memory-mapped files
"""""""""""""""""""

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
   >>> mrc.data[1:3,1:3] = 0

   >>> # Read the entire array - with large files this might take a while!
   >>> mrc.data[:]
   memmap([[ 0,  1,  2,  3],
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
   ... 
   MrcFile('tmp.mrc', mode='r')

   >>> with mrcfile.GzipMrcFile('tmp.mrc.gz') as mrc:
   ...     mrc
   ... 
   GzipMrcFile('tmp.mrc.gz', mode='r')

   >>> with mrcfile.MrcMemmap('tmp.mrc') as mrc:
   ...     mrc
   ... 
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
   ValueError: File 'empty.mrc' already exists; set overwrite=True to overwrite it
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
:attr:`~mrcfile.mrcobject.MrcObject.data` attributes:

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> mrc = mrcfile.open('tmp.mrc')
   >>> mrc.header
   rec.array((4, 3, 1, ...),
             dtype=[('nx', ...)])
   >>> mrc.extended_header
   array([], 
         dtype='|V1')
   >>> mrc.data
   array([[ 0,  1,  2,  3],
          [ 4,  5,  6,  7],
          [ 8,  9, 10, 11]], dtype=int8)
   >>> mrc.close()

These attributes are read-only and cannot be assigned to directly, but (unless
the file mode is ``r``) the arrays can be modified in-place:

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')
   >>> # A new data array cannot be assigned directly to the data attribute
   >>> mrc.data = np.ones_like(example_data)
   Traceback (most recent call last):
     ...
   AttributeError: can't set attribute
   >>> # But the data can be modified by assigning to a slice or index
   >>> mrc.data[0, 0] = 10
   >>> mrc.data
   array([[10,  1,  2,  3],
          [ 4,  5,  6,  7],
          [ 8,  9, 10, 11]], dtype=int8)
   >>> # All of the data values can be replaced this way, as long as the data
   >>> # size, shape and type are not changed
   >>> mrc.data[:] = np.ones_like(example_data)
   >>> mrc.data
   array([[1, 1, 1, 1],
          [1, 1, 1, 1],
          [1, 1, 1, 1]], dtype=int8)
   >>> mrc.close()

To replace the data or extended header completely, call the 
:meth:`~mrcfile.mrcobject.MrcObject.set_data` and
:meth:`~mrcfile.mrcobject.MrcObject.set_extended_header` methods:

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')
   >>> data_3d = np.linspace(-1000, 1000, 20, dtype=np.int16).reshape(2, 2, 5)
   >>> mrc.set_data(data_3d)
   >>> mrc.data
   array([[[-1000,  -894,  -789,  -684,  -578],
           [ -473,  -368,  -263,  -157,   -52]],
          [[   52,   157,   263,   368,   473],
           [  578,   684,   789,   894,  1000]]], dtype=int16)
   >>> # Setting a new data array updates the header dimensions to match
   >>> mrc.header.nx
   array(5, dtype=int32)
   >>> mrc.header.ny
   array(2, dtype=int32)
   >>> mrc.header.nz
   array(2, dtype=int32)
   >>> # We can also set the extended header in the same way
   >>> string_array = np.fromstring(b'The extended header can hold any kind of numpy array', dtype='S52')
   >>> mrc.set_extended_header(string_array)
   >>> mrc.extended_header
   array([b'The extended header can hold any kind of numpy array'], 
         dtype='|S52')
   >>> # Setting the extended header updates the header's nsymbt field to match
   >>> mrc.header.nsymbt
   array(52, dtype=int32)
   >>> mrc.close()

Note that setting an extended header does not automatically set or change the
header's ``exttyp`` field. You should set this yourself to identify the type
of extended header you are using.

For a quick overview of the contents of a file's header, call
:meth:`~mrcfile.mrcobject.MrcObject.print_header`:

.. doctest::

   >>> with mrcfile.open('tmp.mrc') as mrc:
   ...     mrc.print_header()
   ... 
   nx              : 5
   ny              : 2
   nz              : 2
   mode            : 1
   nxstart ...

Voxel size
~~~~~~~~~~

The voxel (or pixel) size in the file can be accessed using the
:attr:`~mrcfile.mrcobject.MrcObject.voxel_size` attribute, which returns a numpy
record array with three fields, ``x``, ``y`` and ``z``, for the voxel size in
each dimension:

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> with mrcfile.open('tmp.mrc') as mrc:
   ...     mrc.voxel_size
   ... 
   rec.array(( 0.,  0.,  0.),
             dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])

In a new file, the voxel size is zero by default. To set the voxel size, you can
assign to the :attr:`~mrcfile.mrcobject.MrcObject.voxel_size` attribute, using a
single number (for an isotropic voxel size), a 3-tuple or a single-item record
array with ``x``, ``y`` and ``z`` fields (which must be in that order):

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')

   >>> # Set a new isotropic voxel size:
   >>> mrc.voxel_size = 1.0
   >>> mrc.voxel_size
   rec.array(( 1.,  1.,  1.),
             dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])

   >>> # Set an anisotropic voxel size using a tuple:
   >>> mrc.voxel_size = (1.0, 2.0, 3.0)
   >>> mrc.voxel_size
   rec.array(( 1.,  2.,  3.),
             dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])

   >>> # And set a different anisotropic voxel size using a record array:
   >>> mrc.voxel_size = np.rec.array(( 4.,  5.,  6.), dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])
   >>> mrc.voxel_size
   rec.array(( 4.,  5.,  6.),
             dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])
   >>> mrc.close()

The sizes are not stored directly in the MRC header, but are calculated when
required from the header's cell and grid size fields. The voxel size can
therefore be changed by altering the cell size:

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')

   >>> # Check the current voxel size in X:
   >>> mrc.voxel_size.x
   array(4.0, dtype=float32)

   >>> # And check the current cell dimensions:
   >>> mrc.header.cella
   rec.array(( 20.,  10.,  6.), 
             dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])

   >>> # Now change the cell's X length:
   >>> mrc.header.cella.x = 10

   >>> # And we see the voxel size has also changed:
   >>> mrc.voxel_size.x
   array(2.0, dtype=float32)

   >>> mrc.close()

Equivalently, the cell size will be changed if a new voxel size is given:

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')

   >>> # Check the current cell dimensions:
   >>> mrc.header.cella
   rec.array(( 10.,  10.,  6.), 
             dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])

   >>> # Set a new voxel size:
   >>> mrc.voxel_size = 1.0

   >>> # And our cell size has been updated:
   >>> mrc.header.cella
   rec.array(( 5.,  2.,  1.), 
             dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])

   >>> mrc.close()

Because the voxel size array is calculated on demand, assigning back to it
wouldn't work so it's flagged as read-only:

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')

   >>> # This doesn't work
   >>> mrc.voxel_size.x = 2.0
   Traceback (most recent call last):
     ...
   ValueError: assignment destination is read-only

   >>> # But you can do this
   >>> vsize = mrc.voxel_size.copy()
   >>> vsize.x = 2.0
   >>> mrc.voxel_size = vsize
   >>> mrc.voxel_size
   rec.array(( 2.,  1.,  1.), 
             dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])
   >>> mrc.close()

Note that the calculated voxel size will change if the grid size is changed by
replacing the data array:

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')

   >>> # Check the current voxel size:
   >>> mrc.voxel_size
   rec.array(( 2.,  1.,  1.), 
             dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])
   >>> # And the current data dimensions:
   >>> mrc.data.shape
   (2, 2, 5)

   >>> # Replace the data with an array with a different shape:
   >>> mrc.set_data(example_data)
   >>> mrc.data.shape
   (3, 4)

   >>> # ...and the voxel size has changed:
   >>> mrc.voxel_size
   rec.array(( 2.5,  0.66666669,  1.), 
             dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4')])

   >>> mrc.close()

Keeping the header and data in sync
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a new data array is given (using
:meth:`~mrcfile.mrcobject.MrcObject.set_data` or the ``data`` argument to
:func:`mrcfile.new`), the header is automatically updated to ensure the file is
is valid:

.. doctest::

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')
   
   >>> # Check the current data shape and header dimensions match
   >>> mrc.data.shape
   (3, 4)
   >>> mrc.header.nx
   array(4, dtype=int32)
   >>> mrc.header.nx == mrc.data.shape[-1]  # X axis is always the last in shape
   True

   >>> # Let's also check the maximum value recorded in the header
   >>> mrc.header.dmax
   array(11.0, dtype=float32)
   >>> mrc.header.dmax == mrc.data.max()
   True

   >>> # Now set a data array with a different shape, and check the header again
   >>> mrc.set_data(data_3d)
   >>> mrc.data.shape
   (2, 2, 5)
   >>> mrc.header.nx
   array(5, dtype=int32)
   >>> mrc.header.nx == mrc.data.shape[-1]
   True

   >>> # The data statistics are updated as well
   >>> mrc.header.dmax
   array(1000.0, dtype=float32)
   >>> mrc.header.dmax == mrc.data.max()
   True
   >>> mrc.close()

If the data array is modified in place, for example by editing values
or changing the shape or dtype attributes, the header will no longer be correct:

.. doctest::

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')
   >>> mrc.data.shape
   (2, 2, 5)
   
   >>> # Change the data shape in-place and check the header
   >>> mrc.data.shape = (5, 4)
   >>> mrc.header.nx == mrc.data.shape[-1]
   False

   >>> # We'll also change some values and check the data statistics
   >>> mrc.data[2:] = 0
   >>> mrc.data.max()
   0
   >>> mrc.header.dmax == mrc.data.max()
   False
   >>> mrc.close()

Note that the header is deliberately not updated automatically except when
:meth:`~mrcfile.mrcobject.MrcObject.set_data` is called, so if you need to
override any of the automatic header values you can do.

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

The file we just saved had an invalid header, but of course, that's what's used
by ``mrcfile`` to work out how to read the file from disk! When we open the file
again, our change to the shape has disappeared:

.. doctest::

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')
   >>> mrc.data.shape
   (2, 2, 5)

   >>> # Let's change the shape again, as we did before
   >>> mrc.data.shape = (5, 4)
   >>> mrc.header.nx == mrc.data.shape[-1]
   False

   >>> # Now let's update the dimensions:
   >>> mrc.update_header_from_data()
   >>> mrc.header.nx
   array(4, dtype=int32)
   >>> mrc.header.nx == mrc.data.shape[-1]
   True

   >>> # The data statistics are still incorrect:
   >>> mrc.header.dmax
   array(1000.0, dtype=float32)
   >>> mrc.header.dmax == mrc.data.max()
   False

   >>> # So let's update those as well:
   >>> mrc.update_header_stats()
   >>> mrc.header.dmax
   array(0.0, dtype=float32)
   >>> mrc.header.dmax == mrc.data.max()
   True
   >>> mrc.close()

In general, if you're changing the shape, type or endianness of the data, it's
easiest to use :meth:`~mrcfile.mrcobject.MrcObject.set_data` and the header will
be kept up to date for you. If you start changing values in the data, remember
that the statistics in the header will be out of date until you call
:meth:`~mrcfile.mrcobject.MrcObject.update_header_stats` or
:meth:`~mrcfile.mrcobject.MrcObject.reset_header_stats`.

Data dimensionality
~~~~~~~~~~~~~~~~~~~

MRC files can be used to store several types of data: single images, image
stacks, volumes and volume stacks. These are distinguished by the dimensionality
of the data array and the space group number (the header's ``ispg`` field):

============  ==========  ===========
Data type     Dimensions  Space group
============  ==========  ===========
Single image      2           0
Image stack       3           0
Volume            3         1--230 (1 for normal EM data)
Volume stack      4        401--630 (401 for normal EM data)
============  ==========  ===========

:class:`~mrcfile.mrcfile.MrcFile` objects have methods to allow easy
identification of the data type:
:meth:`~mrcfile.mrcobject.MrcObject.is_single_image`,
:meth:`~mrcfile.mrcobject.MrcObject.is_image_stack`,
:meth:`~mrcfile.mrcobject.MrcObject.is_volume` and
:meth:`~mrcfile.mrcobject.MrcObject.is_volume_stack`.

.. doctest::

   >>> mrc = mrcfile.open('tmp.mrc')

   >>> # The file currently contains two-dimensional data
   >>> mrc.data.shape
   (5, 4)
   >>> len(mrc.data.shape)
   2

   >>> # This is intepreted as a single image
   >>> mrc.is_single_image()
   True
   >>> mrc.is_image_stack()
   False
   >>> mrc.is_volume()
   False
   >>> mrc.is_volume_stack()
   False

   >>> mrc.close()

If a file already contains image or image stack data, new three-dimensional data
is treated as an image stack; otherwise, 3D data is treated as a volume by
default:

.. doctest::

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')
   
   >>> # New 3D data in an existing image file is treated as an image stack:
   >>> mrc.set_data(data_3d)
   >>> len(mrc.data.shape)
   3
   >>> mrc.is_volume()
   False
   >>> mrc.is_image_stack()
   True
   >>> int(mrc.header.ispg)
   0
   >>> mrc.close()

   >>> # But normally, 3D data is treated as a volume:
   >>> mrc = mrcfile.new('tmp.mrc', overwrite=True)
   >>> mrc.set_data(data_3d)
   >>> mrc.is_volume()
   True
   >>> mrc.is_image_stack()
   False
   >>> int(mrc.header.ispg)
   1
   >>> mrc.close()

Call :meth:`~mrcfile.mrcobject.MrcObject.set_image_stack` and 
:meth:`~mrcfile.mrcobject.MrcObject.set_volume` to change the interpretation of
3D data. (Note: as well as changing ``ispg``, these methods also change ``mz``
to be 1 for image stacks and equal to ``nz`` for volumes.)

.. doctest::

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')

   >>> # Change the file to represent an image stack:
   >>> mrc.set_image_stack()
   >>> mrc.is_volume()
   False
   >>> mrc.is_image_stack()
   True
   >>> int(mrc.header.ispg)
   0

   >>> # And now change it back to representing a volume:
   >>> mrc.set_volume()
   >>> mrc.is_volume()
   True
   >>> mrc.is_image_stack()
   False
   >>> int(mrc.header.ispg)
   1

   >>> mrc.close()

Note that the `MRC format`_ allows the data axes to be swapped using the
header's ``mapc``, ``mapr`` and ``maps`` fields. This library does not attempt
to swap the axes and simply assigns the columns to X, rows to Y and sections to
Z. (The data array is indexed in C style, so data values can be accessed using
``mrc.data[z][y][x]``.) In general, EM data is written using the default
axes, but crystallographic data files might use swapped axes in certain space
groups -- if this might matter to you, you should check the ``mapc``, ``mapr``
and ``maps`` fields after opening the file and consider transposing the data
array if necessary.

.. _MRC format: http://www.ccpem.ac.uk/mrc_format/mrc2014.php

Data types
~~~~~~~~~~

Various numpy `data types`_ can be used for MRC data arrays. The conversions to
MRC mode numbers are:

.. _data types: https://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html

=========  ========
Data type  MRC mode
=========  ========
float16       2 (note that data will be widened to 32 bits in the file)
float32       2
int8          0
int16         1
uint8         6 (note that data will be widened to 16 bits in the file)
uint16        6
complex64     4
=========  ========

(Mode 3 is not supported since there is no corresponding numpy dtype.)

No other data types are accepted, including integer types of more than 16 bits,
or float types of more than 32 bits. Many numpy array creation routines use
int64 or float64 dtypes by default, which means you will need to give a
``dtype`` argument to ensure the array can be used in an MRC file:

.. doctest::

   >>> mrc = mrcfile.open('tmp.mrc', mode='r+')

   >>> # This does not work
   >>> mrc.set_data(np.zeros((4, 5)))
   Traceback (most recent call last):
     ...
   ValueError: dtype 'float64' cannot be converted to an MRC file mode
   >>> # But this does
   >>> mrc.set_data(np.zeros((4, 5), dtype=np.int16))
   >>> mrc.data
   array([[0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0]], dtype=int16)

   >>> mrc.close()

Validating MRC files
--------------------

MRC files can be validated with :func:`mrcfile.validate`:

.. doctest::

   >>> mrcfile.validate('tmp.mrc')
   True

This works equally well for gzipped files:

.. doctest::

   >>> mrcfile.validate('tmp.mrc.gz')
   True

Serious errors (such as a corrupt file) will cause an exception to be raised as
the file is opened:

.. doctest::

   >>> # First, let's make the file invalid
   >>> with mrcfile.open('tmp.mrc', mode='r+') as mrc:
   ...     mrc.header.map = b'bad '
   ... 

   >>> # Now when we try to validate it, we'll get an exception:
   >>> mrcfile.validate('tmp.mrc')
   Traceback (most recent call last):
      ...
   ValueError: Map ID string not found - not an MRC file, or file is corrupt

More minor errors will cause messages to be printed to the console, and
:func:`~mrcfile.validate` will return ``False``:

.. doctest::

   >>> # Let's make a file which is valid except for the header's mz value
   >>> with mrcfile.new('tmp.mrc', overwrite=True) as mrc:
   ...     mrc.set_data(example_data)
   ...     mrc.header.mz = -1
   ... 

   >>> # Now it should fail validation and print a helpful message
   >>> mrcfile.validate('tmp.mrc')
   Header field 'mz' is negative
   False

Normally, messages are printed to ``sys.stdout`` (as normal for Python ``print``
calls). :func:`~mrcfile.validate` has an optional ``print_file`` argument which
allows any text stream to be used for the output instead:

.. doctest::

   >>> # Create a text stream to capture the output
   >>> import io
   >>> output = io.StringIO()

   >>> # Now validate the file...
   >>> mrcfile.validate('tmp.mrc', print_file=output)
   False

   >>> # ...and check the output separately
   >>> print(output.getvalue().strip())
   Header field 'mz' is negative

Behind the scenes, :func:`mrcfile.validate` calls :func:`mrcfile.open` and then
:meth:`MrcFile.validate() <mrcfile.mrcfile.MrcFile.validate>`. If you already
have an :class:`~mrcfile.mrcfile.MrcFile` open, you can call this directly to
check the file -- but note that the file size test might be inaccurate unless
you call :meth:`~mrcfile.mrcinterpreter.MrcInterpreter.flush` first. Also,
:meth:`MrcFile.validate() <mrcfile.mrcfile.MrcFile.validate>` doesn't check for
serious problems which would stop the file being opened. To ensure the file is
valid, it's best to flush the file and then validate it using
:func:`mrcfile.validate`.

API overview
============

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
* :meth:`~mrcfile.mrcfile.MrcFile.validate`
* :meth:`~mrcfile.mrcinterpreter.MrcInterpreter.flush`
* :meth:`~mrcfile.mrcinterpreter.MrcInterpreter.close`
