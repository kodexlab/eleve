*******
Storage
*******

Storage are mains ``ELeVE`` components. They manage langage model (`trie <https://en.wikipedia.org/wiki/Trie>`_ of n-grams)
storage and query.

``ELeVE`` provide different storages that may be used. To a proper documentation
of ``ELeVE``'s storage objects API please look at :class:`eleve.memory.MemoryStorage`
which is a full-Python implementation that provides the reference API that all
other storage follow.

Basicly two types of storage may be used in function of the needs:

  * **Memory storage** that are fast but limited by RAM size,
  * **Disk storage** that are slower but only limited by disk space.


Memory Storage
==============

.. note::  To use a memory storage you should import :class:`eleve.MemoryStorage`::

    >>> from eleve import MemoryStorage
    >>> storage = MemoryStorage(5)

  It is an alias to the best available memory storage (should be :class:`eleve.c_memory.cmemory.MemoryStorage`).


Construction
------------

Memory storage constructor takes only one parameter: ther ``odrer`` i.e. the
lenght of the n-grams that are stored::

    >>> from eleve import MemoryStorage
    >>> storage = MemoryStorage(3)

Training
--------

To build a storage from a corpus the :func:`.add_sentence` method should be use::

    >>> storage.add_sentence(["very", "small", "black", "cat"])
    >>> storage.add_sentence(["super", "small", "red", "cat"])
    >>> storage.add_sentence(["big", "black", "cat"])
    >>> storage.add_sentence(["crazy", "dog"])


Querying
--------

Storages provide a method to query a n-gram count::

    >>> storage.query_count(["cat"])
    3.0
    >>> storage.query_count(["black", "cat"])
    2.0
    >>> storage.query_count(["very", "small", "black", "cat"])
    0.0

You can notice that count are available of every size of n-grams, however n-grams
larger than the storage ``order`` will have a count of zero.

One can also query autonomy of an n-gram::

    >>> storage.query_autonomy(["black", "cat"])
    1.9537...
    >>> storage.query_autonomy(["small", "black"])
    -0.1965...

Note that with an ``order`` of ``N``, autonomy of n-gram of size ``N-1`` at maximum may be computed::

    >>> storage.query_autonomy(["small", "black", "cat"])
    nan

Save and load
-------------

For now it is not possible to save or restore a MemoryStorage. It should be re-train each time. This will change in a near future !



Python and C++ implementations
------------------------------

Two memory storage are provided: :class:`eleve.memory.MemoryStorage` and 
:class:`eleve.c_memory.cmemory.MemoryStorage`. The former is full-Python and
provide the reference API, the latter is writen in C++ and is much more efficient.

Only the C++ one should be used. The best practice is to use
:class:`eleve.MemoryStorage` which is an alias to the C++ one that provides a
fail back one the full-Python one if compilation of C++ one has failed.


Disk Storage (*Leveldb*)
========================

.. note::  To use a disk storage you should import :class:`eleve.LeveldbStorage`::

    >>> from eleve import LeveldbStorage
    >>> hdd_storage = LeveldbStorage(3, "./tmp_storage")
  
  It is an alias to the best available disk storage (should be :class:`eleve.c_leveldb.cleveldb.LeveldbStorage`).

.. doctest::
    :hide:

    >>> hdd_storage.clear()
    >>> del hdd_storage

``ELeVE`` provide on-disk storages. They are much slower than the memory ones
but not limited by memory size. And as everything is stored on-disk, they are
persistant, they can be restored without loading. On-disk storage internaly use
`LevelDB <https://github.com/google/leveldb>`_ to store the model.

Use that storage in two cases:

* If you want to create a model for a HUGE training corpus that don't fit in RAM.
* If you don't want to re-train your model everytime on a corpus everytime you use it. Be aware that
  it may be faster to re-train it each time in RAM, because the query time for the Leveldb storage is higher.

.. warning::
    You can't create more than one instance of a storage for the specific path.
    Leveldb use locking, so if two process try to access the same database, the
    second will fail.

The API is the same as for the Memory storage. Only the constructor changes.


Construction, save, load and clear
----------------------------------

Disk storage constructor takes an ``odrer`` parameter as memory storage, it also
need a path, where model data will be stored on disk::

    >>> from eleve import LeveldbStorage
    >>> hdd_storage = LeveldbStorage(3, "./tmp_storage")

Then everything is the same than with memory storage:: 

    >>> hdd_storage.add_sentence(["very", "small", "black", "cat"])
    >>> hdd_storage.add_sentence(["super", "small", "red", "cat"])
    >>> hdd_storage.add_sentence(["big", "black", "cat"])
    >>> hdd_storage.add_sentence(["crazy", "dog"])
    >>> hdd_storage.query_count(["black", "cat"])
    2
    >>> hdd_storage.query_count(["very", "small", "black", "cat"])
    0
    >>> hdd_storage.query_autonomy(["black", "cat"])
    1.9537...
    >>> hdd_storage.query_autonomy(["small", "black"])
    -0.1965...
    >>> hdd_storage.query_autonomy(["small", "black", "cat"])
    nan


It is possible to open a storage from an existing path on the disk::

    >>> del hdd_storage # a storage can not be open twice, so we need to free it
    >>> hdd_storage2 = LeveldbStorage(3, "./tmp_storage")
    >>> hdd_storage2.query_autonomy(["black", "cat"])
    1.9537...
    >>> hdd_storage2.query_autonomy(["small", "black"])
    -0.1965...

Note that there is no (need for) special save method.


Finaly if you want to remove a storage ::

   >>> hdd_storage2.clear()
   >>> hdd_storage2.query_autonomy(["black", "cat"])
   nan

