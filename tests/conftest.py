""" Pytest configuration file, define fixtures
"""
import os
import pytest
import tempfile
import shutil
from copy import copy

from eleve.memory import MemoryTrie
from eleve import MemoryStorage

## Trie fixture
def parametrize_trie(**kwargs):
    return pytest.mark.parametrize(
        "trie", get_tries(**kwargs), indirect=True, ids=storage_name
    )


def get_tries(py=True, c=True, ref=True, volatile=True, persistant=True):
    """ Generates a list of trie fixture configuration
    
    :attr py: include Python backend
    :attr c: include C/C++ backend
    :attr ref: include reference backend (python in ram)
    :attr volatile: include RAM backend
    :attr persistant: include Disk backend
    """
    tries = []
    # choose basic class
    if py and ref and volatile:
        tries.append({"name": "pyram"})
    if py and persistant:
        tries.append({"name": "pyleveldb"})
    if c and volatile:
        tries.append({"name": "cram"})
    if c and persistant:
        tries.append({"name": "cleveldb"})
    return tries


@pytest.fixture
def trie(request):
    backend = request.param["name"]
    if backend == "pyram":
        trie = MemoryTrie()
    else:
        raise ValueError("Invalid `trie` fixture param")
    return trie


## Storage fixture


def parametrize_storage(**kwargs):
    return pytest.mark.parametrize(
        "storage", get_storages(**kwargs), indirect=True, ids=storage_name
    )


def get_storages(
    py=True,
    c=True,
    ref=True,
    volatile=True,
    persistant=True,
    default_ngram_length=None,
    create_dir=True,
):
    """ Generates a list of storage fixture configuration

    :attr py: include Python backend
    :attr c: include C/C++ backend
    :attr ref: include reference backend (python in ram)
    :attr volatile: include RAM backend
    :attr persistant: include Disk backend
    :attr default_ngram_length: param default_ngram_length of Storage, may be a list of different values
    :attr create_dir: whether to create the directory (for disk backend), if None both cases are given
    """
    storages = []
    dd_storages = []
    # choose basic class
    if py and ref and volatile:
        storages.append({"name": "pyram"})
    if py and persistant:
        dd_storages.append({"name": "pyleveldb"})
    if c and volatile:
        storages.append({"name": "cram"})
    if c and persistant:
        dd_storages.append({"name": "cleveldb"})
    # compute different config
    if create_dir is None:
        for storage in dd_storages:
            storage_create = copy(storage)
            storage_create["create"] = True
            storages.append(storage_create)
            storage_nocreate = storage
            storage_nocreate["create"] = False
            storages.append(storage_nocreate)
    else:
        for storage in dd_storages:
            storage["create"] = create_dir
            storages.append(storage)
    # conf ngram_length
    if isinstance(default_ngram_length, int):
        storages_old = storages
        storages = []
        for storage in storages_old:
            storage = copy(storage)
            storage["default_ngram_length"] = default_ngram_length
            storages.append(storage)
    elif isinstance(default_ngram_length, list):
        storages_old = storages
        storages = []
        for storage in storages_old:
            for ngram_length in default_ngram_length:
                storage = copy(storage)
                storage["default_ngram_length"] = ngram_length
                storages.append(storage)
    return storages


def storage_name(param):
    name = param["name"]
    if "create" in param and not param["create"]:
        name += "_nocreate"
    if "default_ngram_length" in param:
        name += "_l%d" % param["default_ngram_length"]
    return name


@pytest.fixture
def storage(request):
    """ Eleve Storage fixture
    """
    backend = request.param["name"]
    create_dir = request.param.get("create", False)
    default_ngram_length = request.param.get("default_ngram_length", None)
    init_params = {}
    if default_ngram_length is not None:
        init_params["default_ngram_length"] = default_ngram_length

    if backend == "pyram":
        storage = MemoryStorage(**init_params)
    else:
        raise ValueError("Invalid `storage` fixture param, got: %s" % backend)
    return storage
