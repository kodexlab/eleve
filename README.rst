What is ELeVE ?
===============

ELeVE is a library intended for computing an "autonomy estimate" score for substrings (all n-grams) in a corpus of text.

The autonomy score is based on normalised variation of branching entropies (nVBE) of strings, See [MagistrySagot2012]_ for a definiton of these terms 

It was developed mainly for unsupervised segmentation of mandarin Chinese, but is language independant and was successfully used in research on other tasks like keyphrase extraction.

Full documentation is available on `http://pythonhosted.org/eleve/ <http://pythonhosted.org/eleve/>`_.

In a nutshell
==============

Here is a simple "getting started". First you have to train a model::

    >>> from eleve import MemoryStorage
    >>>
    >>> storage = MemoryStorage()
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

Eleve also store n-gram's occurence count::

    >>> storage.query_count(["New", "York"])
    2
    >>> storage.query_count(["New", "potatoes"])
    0
    >>> storage.query_count(["I", "like", "potatoes"])
    1
    >>> storage.query_count(["potatoes"])
    2

Then, you can use it for segmentation, using an algorithm that look for the solution which maximize nVBE of resulting words::

    >>> from eleve import Segmenter
    >>> s = Segmenter(storage)
    >>> # segment up to 4-grams, if we used the same storage as before.
    >>>
    >>> s.segment(["What", "do", "you", "know", "about", "New", "York"])
    [['What'], ['do'], ['you'], ['know'], ['about'], ['New', 'York']]



Installation
============

You will need some dependencies. On Ubuntu::

    $ sudo apt-get install python3-dev libboost-python-dev libboost-filesystem-dev libleveldb-dev

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

Pull requests are welcome!

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

If you use ``eleve`` for an academic publication, please cite this paper:

.. [MagistrySagot2012] Magistry, P., & Sagot, B. (2012, July). Unsupervized word segmentation: the case for mandarin chinese. In Proceedings of the 50th Annual Meeting of the ACL: Short Papers-Volume 2 (pp. 383-387). http://www.aclweb.org/anthology/P12-2075



Copyright, license and authors
==============================

Copyright (C) 2014-2015 Kodex⋅Lab.

``eleve`` is available under the `LGPL Version 3 <http://www.gnu.org/licenses/lgpl.txt>`_ license.

``eleve`` was originaly designed and prototyped by `Pierre Magistry <http://magistry.fr/>`_ during its PhD. It then has been completly rewriten by  `Korantin Auguste <http://www.palkeo.com/>`_ and `Emmanuel Navarro <http://enavarro.me/>`_ (with the help of Pierre).

