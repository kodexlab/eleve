What is ELeVE ?
===============

ELeVE is a library for calculating a specialized language model from a corpus of text.

It allows you to use statistics from the training corpus to calculate branching entropy, and autonomy measures for n-grams of text.
See [MagistrySagot2012]_ for a definiton of these terms (autonomy is also called « nVBE » for « normalized entropy variation »)

It was mainly developed for segmentation of mandarin Chinese, but was successfully used to research on other tasks like keyphrase extraction.


In a nutshell
==============

Here is simple "getting started". First you have to train a model::

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

And then you cat query it::

    >>> storage.query_autonomy(["New", "York"])
    2.0369977951049805
    >>> storage.query_autonomy(["like", "potatoes"])
    -0.3227022886276245

Eleve also store n-gram's frequency::

    >>> storage.query_count(["New", "York"])
    2.0
    >>> storage.query_count(["New", "potatoes"])
    0.0
    >>> storage.query_count(["I", "like", "potatoes"])
    1.0
    >>> storage.query_count(["potatoes"])
    2.0

The you can use it for segmentation::

    >>> from eleve import Segmenter
    >>> s = Segmenter(storage, 4)
    >>> # segment up to 4-grams, if we used the same storage as before.
    >>>
    >>> s.segment(["What", "do", "you", "know", "about", "New", "York"])
    [['What'], ['do'], ['you'], ['know'], ['about'], ['New', 'York']]



Installation
============

You will need some dependancies. On ubuntu::

    $ sudo apt-get install libboost-python-dev libleveldb-dev

Then to install eleve::

    $ pip install eleve

or if you have a local clone of source folder::

    $ python setup.py install


Get the source
==============

Source are stored on `github <https://github.com/kodexlab/eleve>`_::

    $ git clone https://github.com/kodexlab/eleve



Contribute
==========

Install the development environment::

    $ git clone https://github.com/kodexlab/eleve
    $ cd eleve
    $ virtualenv ENV -p /usr/bin/python3
    $ source ENV/bin/activate
    $ pip install -r requirements.txt
    $ pip install -r requirements.dev.txt

Pull requests are welcomed !

To run tests::

    $ make testall

To build the doc::

    $ make doc

then open: ``docs/_build/html/index.html``


**Warning**: You need to have ``eleve`` accesible in the python path to run tests (and to build doc).
For that you can install ``eleve`` as a link in local virtualenv::

    $ pip install -e .

(Note: this is indicated in pytest `good practice <https://pytest.org/latest/goodpractises.html>`_ )


References
===========

If you use ``eleve`` for an academic word tanks to cite this paper:

.. [MagistrySagot2012] Magistry, P., & Sagot, B. (2012, July). Unsupervized word segmentation: the case for mandarin chinese. In Proceedings of the 50th Annual Meeting of the ACL: Short Papers-Volume 2 (pp. 383-387). http://www.aclweb.org/anthology/P12-2075



Copyright, license and authors
==============================

Copyright (C) 2014-2015 Kodex⋅Lab.

``eleve`` is available under the `LGPL Version 3<http://www.gnu.org/licenses/lgpl.txt>`_ license.

``eleve`` was originaly designed and prototyped by `Pierre Magistry <http://magistry.fr/>`_ during it's PhD. It then has been completly revriten by  `Palkeo <http://www.palkeo.com/>`_ and `Emmanuel Navarro <http://enavarro.me/>`_ (with the help of Pierre).

