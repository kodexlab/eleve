import cython

cdef float NaN
cdef object PACKER
cdef bytes SEPARATOR
cdef bytes SEPARATOR_PLUS_ONE

cdef bytes to_bytes(object o)
cdef bytes ngram_to_key(list ngram)

cdef class Node:
    cdef public int count
    cdef public float entropy
    cdef object db
    cdef public bytes key

    cdef save(self, db=*)

    @cython.locals(entropy=cython.float, sum_counts=cython.int)
    cdef update_entropy(self, terminals)

cdef class LevelTrie:
    cdef object db
    cdef bint dirty
    cdef str path
    cdef object normalization
    cdef object terminals

    @cython.locals(b=bytearray, w=object, node=Node, i=cython.int, create=bint)
    cpdef add_ngram(self, list ngram, int freq=*)
    
    @cython.locals(ev=float, mean=float, stdev=float, count=int, old_mean=float)
    cdef _update_stats_rec(self, float parent_entropy, int depth, Node node)

    cdef _check_dirty(self)

    cdef Node node(self, list ngram)
