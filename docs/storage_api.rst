===========
Storage API
===========

Memory Storage
--------------

Available at ``eleve.MemoryStorage``.

.. autoclass:: eleve.memory_storage.MemoryStorage
    :members:

Leveldb Storage
---------------

Available at ``eleve.LeveldbStorage``.

An on-disk storage. It is much slower than the in-memory storage.
However, everything is stored on-disk, so the state can be restored by loading
an existing storage.

Use that storage in two cases :

* If you want to create a model for a HUGE training corpus that don't fit in RAM.
* If you don't want to re-train your model everytime on a corpus everytime you use it. Be aware that
  it may be faster to re-train it each time in RAM, because the query time for the Leveldb storage is higher.

.. warning::
    You can't create more than one instance of a storage for the specific path.
    Leveldb use locking, so if two process try to access the same database, the
    second will fail.

The API is the same as for the Memory storage. Only the constructor changes.

.. autoclass:: eleve.leveldb_storage.LeveldbStorage
    :members:

