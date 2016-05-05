parmap
======

.. image:: https://travis-ci.org/zeehio/parmap.svg?branch=master
    :target: https://travis-ci.org/zeehio/parmap

.. image:: https://readthedocs.org/projects/parmap/badge/?version=latest
    :target: https://readthedocs.org/projects/parmap/?badge=latest
    :alt: Documentation Status

.. image:: https://codecov.io/github/zeehio/parmap/coverage.svg?branch=master
    :target: https://codecov.io/github/zeehio/parmap?branch=master

.. image:: https://codeclimate.com/github/zeehio/parmap/badges/gpa.svg
   :target: https://codeclimate.com/github/zeehio/parmap
   :alt: Code Climate

.. image:: https://img.shields.io/pypi/dm/parmap.svg
    :target: https://pypi.python.org/pypi/parmap
    :alt: Pypi downloads per month

This small python module implements two functions: ``map`` and
``starmap``.

What does parmap offer?
-----------------------

-  Provide an easy to use syntax for both ``map`` and ``starmap``.
-  Parallelize transparently whenever possible.
-  Handle multiple (positional -for now-) arguments as needed.

Installation:
-------------

::

  pip install parmap


Usage:
------

Here are some examples with some unparallelized code parallelized with
parmap:

::

  import parmap
  # You want to do:
  y = [myfunction(x, argument1, argument2) for x in mylist]
  # In parallel:
  y = parmap.map(myfunction, mylist, argument1, argument2)

  # You want to do:
  z = [myfunction(x, y, argument1, argument2) for (x,y) in mylist]
  # In parallel:
  z = parmap.starmap(myfunction, mylist, argument1, argument2)

  # You want to do:
  listx = [1, 2, 3, 4, 5, 6]
  listy = [2, 3, 4, 5, 6, 7]
  param = 3.14
  param2 = 42
  listz = []
  for (x, y) in zip(listx, listy):
      listz.append(myfunction(x, y, param1, param2))
  # In parallel:
  listz = parmap.starmap(myfunction, zip(listx, listy), param1, param2)


map (and starmap on python 3.3) already exist. Why reinvent the wheel?
----------------------------------------------------------------------

Please correct me if I am wrong, but from my point of view, existing
functions have some usability limitations:

-  The built-in python function ``map`` [#builtin-map]_
   is not able to parallelize.
-  ``multiprocessing.Pool().starmap`` [#multiproc-starmap]_
   is only available in python-3.3 and later versions.
-  ``multiprocessing.Pool().map`` [#multiproc-map]_
   does not allow any additional argument to the mapped function.
-  ``multiprocessing.Pool().starmap`` allows passing multiple arguments,
   but in order to pass a constant argument to the mapped function you
   will need to convert it to an iterator using
   ``itertools.repeat(your_parameter)`` [#itertools-repeat]_

``parmap`` aims to overcome this limitations in the simplest possible way.

Additional features in parmap:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Create a pool for parallel computation automatically if possible.
-  ``parmap.map(..., ..., parallel=False)`` # disables parallelization
-  ``parmap.map(..., ..., chunksize=3)`` # size of chunks (see
   multiprocessing.Pool().map)
-  ``parmap.map(..., ..., pool=multiprocessing.Pool())`` # use an existing
   pool, in this case parmap will not close the pool.

To do:
------

Pull requests and suggestions are welcome.

-  Pass keyword arguments to functions?

Acknowledgments:
----------------

The original idea for this implementation was 
`given <http://stackoverflow.com/a/5443941/446149>`_ by J.F. Sebastian. I just
provided an alternative `answer <http://stackoverflow.com/a/21292849/446149>`_
implementing it in a package.

Known works using parmap
---------------------------

- Davide Gerosa, Michael Kesden, "PRECESSION. Dynamics of spinning black-hole
  binaries with python." `arXiv:1605.01067 <https://arxiv.org/abs/1605.01067>`_, 2016

References
-----------

.. [#builtin-map] http://docs.python.org/dev/library/functions.html#map
.. [#multiproc-starmap] http://docs.python.org/dev/library/multiprocessing.html#multiprocessing.pool.Pool.starmap
.. [#multiproc-map] http://docs.python.org/dev/library/multiprocessing.html#multiprocessing.pool.Pool.map
.. [#itertools-repeat] http://docs.python.org/2/library/itertools.html#itertools.repeat

