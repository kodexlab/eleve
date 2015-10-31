=============
Internal Trie
=============

**Internal data structure.**

Eleve storages used two tries (one to model the language left-to-right and one
right-to-left). It may be useful to use these tries directly. For instance if you
need a model in only one direction.

Memory and disk tries are provided. As for storages, the reference
implementation is provided by :class:`eleve.memory.MemoryTrie`.

The Leveldb trie have the same API. Refer to the source code for more information.

