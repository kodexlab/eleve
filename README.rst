What is ELeVE ?
===============

ELeVE is a library for calculating a specialized language model from a corpus of text.

It allows you to use statistics from the training corpus to calculate branching entropy, and autonomy measures for n-grams of text.
See this paper for a definiton of these terms : http://www.aclweb.org/anthology/P12-2075 (autonomy is also called « nVBE » for « normalized
entropy variation »)

It was mainly developed for segmentation of mandarin Chinese, but was successfully used to research on other tasks like keyphrase extraction.

ELeVE API in a nutshell
=======================

::

    from eleve import MemoryStorage, LeveldbStorage

    # the parameter is the length of n-grams we will store. In that case, we can calculate autonomy of 4-grams (because we need to know what follows the 4-grams)
    storage = MemoryStorage(5)

    # we could also have used a storage in disk :
    # storage = LeveldbStorage(5, "/tmp/storage")

    storage.add_sentence(["I", "like", "new", "york"])
    storage.add_sentence(["I", "like", "potatoes"])
    storage.add_sentence(["new", "york", "is", "a", "fine", "city"])

    storage.query_autonomy(["new", "york"])

    # see also query_entropy, query_ev, query_count...

For segmentation: ::

    from eleve import Segmenter

    s = Segmenter(storage, 4) # segment up to 4-grams, if we used the same storage as before.

    s.segment(["What", "do", "you", "know", "about", "new", "york"])

