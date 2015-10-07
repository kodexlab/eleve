What is ELeVE ?
===============

ELeVE is a library for calculating a specialized language model from a corpus of text.

It allows you to use statistics from the training corpus to calculate branching entropy, and autonomy measures for n-grams of text.
See this paper for a definiton of these terms : http://www.aclweb.org/anthology/P12-2075 (autonomy is also called « nVBE » for « normalized
entropy variation »)

It was mainly developed for segmentation of mandarin Chinese, but was successfully used to research on other tasks like keyphrase extraction.


In a nutshell
==============

Here is simple "getting started".

First you have to train a model :

>>> from eleve import MemoryStorage
>>>
>>> storage = MemoryStorage(5)
>>> # the parameter is the length of n-grams we will store.
>>> # In that case, we can calculate autonomy of 4-grams
>>> # (because we need to know what follows the 4-grams)
>>>
>>> # Then the training itself:
>>> storage.add_sentence(["I", "like", "New", "York", "city"])
>>> storage.add_sentence(["I", "like", "potatoes"])
>>> storage.add_sentence(["potatoes", "are", "fine"])
>>> storage.add_sentence(["New", "York", "is", "a", "fine", "city"])

And then you cat query it:

>>> storage.query_autonomy(["New", "York"])
2.0369977951049805
>>> storage.query_autonomy(["like", "potatoes"])
-0.3227022886276245

Eleve also store n-gram's frequency:

>>> storage.query_count(["New", "York"])
2.0
>>> storage.query_count(["New", "potatoes"])
0.0
>>> storage.query_count(["I", "like", "potatoes"])
1.0
>>> storage.query_count(["potatoes"])
2.0

The you can use it for segmentation:

>>> from eleve import Segmenter
>>> s = Segmenter(storage, 4) # segment up to 4-grams, if we used the same storage as before.
>>> s.segment(["What", "do", "you", "know", "about", "New", "York"])
[['What'], ['do'], ['you'], ['know'], ['about'], ['New', 'York']]


For more information, refer to documenation.



Installation
============

You will need some dependancies. On ubuntu::

    $ sudo apt-get install libboost-python-dev libleveldb-dev

Then to install eleve :

    $ pip install eleve

or if you have a local clone of source folder:

    $ python setup.py install


Get the source
==============

Source are stored on github :

    $ git clone https://github.com/kodexlab/eleve


License
=======

`eleve` source code is available under the `LGPL Version 3<http://www.gnu.org/licenses/lgpl.txt>` license.

Contribute
==========

TODO

