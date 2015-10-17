""" Pytest configuration file, define fixtures
"""
import os
import pytest
import tempfile
import shutil

from eleve.memory import MemoryTrie
from eleve.leveldb import LeveldbTrie as PyLeveldbTrie
from eleve.c_memory.cmemory import MemoryTrie as CMemoryTrie
from eleve.c_leveldb.cleveldb import LeveldbTrie as CLeveldbTrie

from eleve import PyMemoryStorage, CMemoryStorage
from eleve import PyLeveldbStorage, CLeveldbStorage

all_trie = [
  "pyram",
#  "cram",
  "pyleveldb",
#  "cleveldb"
]

tested_trie = [ # against pyram trie
#  "cram",
  "pyleveldb",
#  "cleveldb"
]

all_storage = [
    "pyram",
#    "cram",
    # text with both backend directory existing (and empty) or not
    ("pyleveldb", True),
#    ("cleveldb", True),
    ("pyleveldb", False),
#    ("cleveldb", False)
]

all_storage_nocreate = [
    "pyram",
#    "cram",
    "pyleveldb",
#    "cleveldb",
]

tested_storage = [ # agains PyRam
#    "cram",
    "pyleveldb"
#    "cleveldb"
]

tested_ngram_length = [2, 5]


# Fixture to generate different ngram length
@pytest.fixture(params=tested_ngram_length)
def ngram_length(request):
    return request.param


@pytest.fixture
def trie(request):
    if request.param == "pyram":
        trie = MemoryTrie()
    elif request.param == "cram":
        trie = CMemoryTrie()
    elif request.param == "pyleveldb":
        fs_path = tempfile.mkdtemp(prefix="tmp_eleve_pyldb_")
        trie = PyLeveldbTrie(path=fs_path)
        def fin():
            """teardown pyleveldb"""
            shutil.rmtree(fs_path)
        request.addfinalizer(fin)
    elif request.param == "cleveldb":
        fs_path = tempfile.mkdtemp(prefix="tmp_eleve_cldb_")
        trie = CLeveldbTrie(path=fs_path)
        def fin():
            """teardown cleveldb"""
            shutil.rmtree(fs_path)
        request.addfinalizer(fin)
    else:
        raise ValueError("Invalid `trie` fixture param")
    return trie


def storage_name(param):
    if isinstance(param, str):
        return param
    elif len(param) == 2:
        return "%s%s" % (param[0], "_nodir" if not param[1] else "")
    elif len(param) == 3:
        return "%s%s_l%d" % (param[0], "_nodir" if not param[1] else "", param[2])
    return ValueError('Invalid storage fixture param')

@pytest.fixture
def storage(request):
    """ Eleve Storage fixture
    
    param are either:
      * a string in: "pyram", "cram", "pyleveldb", "cleveldb"
      * a tuple of (string, bool), the string is the backend to use and the bool
        indicate if the backend directory should be created or not
    """
    if isinstance(request.param, str):
        backend = request.param
        create_dir = False
    else:
        backend = request.param[0]
        create_dir = request.param[1]

    if backend == "pyram":
        storage = PyMemoryStorage()

    elif backend == "cram":
        storage = CMemoryStorage()

    elif backend == "pyleveldb":
        fs_path = tempfile.mkdtemp(prefix="tmp_eleve_strg_pyldb_")
        if not create_dir:
            fs_path = os.path.join(fs_path, 'new_dir')
        storage = PyLeveldbStorage(path=fs_path)
        def fin():
            """teardown pyleveldb"""
            storage.close()
            shutil.rmtree(fs_path)
        request.addfinalizer(fin)

    elif backend == "cleveldb":
        fs_path = tempfile.mkdtemp(prefix="tmp_eleve_strg_cldb_")
        if not create_dir:
            fs_path = os.path.join(fs_path, 'new_dir')
        storage = CLeveldbStorage(path=fs_path)
        def fin():
            """teardown cleveldb"""
            storage.close()
            shutil.rmtree(fs_path)
        request.addfinalizer(fin)

    else:
        raise ValueError("Invalid `storage` fixture param, got: %s" % request.param)
    return storage


