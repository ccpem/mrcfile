mrcfile.py API overview
=======================

Using MrcFile objects
---------------------

Opening and closing
~~~~~~~~~~~~~~~~~~~

MRC files should usually be opened using the :func:`mrcfile.new` or
:func:`mrcfile.open` functions. These return an instance of the
:class:`~mrcfile.mrcfile.MrcFile` class, which represents an MRC file on disk
and makes the file's header, extended header and data available for read and
write access as numpy arrays.

MrcFile objects always encapsulate a file on disk, and should be closed when
they are finished with by calling
:meth:`~mrcfile.mrcinterpreter.MrcInterpreter.close`. MrcFile supports Python's
context manager so MrcFile objects can conveniently be created and automatically
closed using Python's ``with`` keyword (like normal Python file objects).

There is also a :meth:`~mrcfile.mrcinterpreter.MrcInterpreter.flush` method that
ensures the MRC data has been written to disk but leaves the file open.

:class:`~mrcfile.gzipmrcfile.GzipMrcFile` objects can be created by opening a
gzip file with the :func:`mrcfile.open` function, or using ``gzip=True`` as an
argument to :func:`mrcfile.new`. :class:`~mrcfile.mrcmemmap.MrcMemmap` objects
can be created using the :func:`mrcfile.mmap` function. All of the classes
in the mrcfile package can also be instantiated by calling the class directly,
if necessary, but the top-level :mod:`mrcfile` functions are preferred.

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
dtype argument to ensure the array can be used in an MRC file::

    # This does not work
    >>> mrc.set_data(np.zeros((10, 10)))
    Traceback (most recent call last):
      ...
    ValueError: dtype 'float64' cannot be converted to an MRC file mode
    
    # But this does
    >>> mrc.set_data(np.zeros((10, 10), dtype=np.int16))
    >>> 

.. _data types: https://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html

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
