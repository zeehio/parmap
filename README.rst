parmap
======

.. image:: https://github.com/zeehio/parmap/actions/workflows/test.yml/badge.svg
    :target: https://github.com/zeehio/parmap/actions/workflows/test.yml

.. image:: https://img.shields.io/conda/vn/conda-forge/parmap.svg
    :target: https://anaconda.org/conda-forge/parmap
    :alt: conda-forge version

.. image:: https://readthedocs.org/projects/parmap/badge/?version=latest
    :target: https://readthedocs.org/projects/parmap/?badge=latest
    :alt: Documentation Status

.. image:: https://codecov.io/github/zeehio/parmap/coverage.svg?branch=master
    :target: https://codecov.io/github/zeehio/parmap?branch=master

.. image:: https://codeclimate.com/github/zeehio/parmap/badges/gpa.svg
   :target: https://codeclimate.com/github/zeehio/parmap
   :alt: Code Climate


This small python module implements four functions: ``map`` and
``starmap``, and their async versions ``map_async`` and ``starmap_async``.

What does parmap offer?
-----------------------

-  Provide an easy to use syntax for both ``map`` and ``starmap``.
-  Parallelize transparently whenever possible.
-  Pass additional positional and keyword arguments to parallelized functions.
-  Show a progress bar (requires `tqdm` as optional package)

Installation:
-------------

::

  pip install tqdm # for progress bar support
  pip install parmap


Usage:
------

Here are some examples with some unparallelized code parallelized with
parmap:

Simple parallelization example:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  import parmap
  # You want to do:
  mylist = [1,2,3]
  argument1 = 3.14
  argument2 = True
  y = [myfunction(x, argument1, mykeyword=argument2) for x in mylist]
  # In parallel:
  y = parmap.map(myfunction, mylist, argument1, mykeyword=argument2)


Show a progress bar:
~~~~~~~~~~~~~~~~~~~~~

Requires ``pip install tqdm``

::

  # You want to do:
  y = [myfunction(x) for x in mylist]
  # In parallel, with a progress bar
  y = parmap.map(myfunction, mylist, pm_pbar=True)
  # Passing extra options to the tqdm progress bar
  y = parmap.map(myfunction, mylist, pm_pbar={"desc": "Example"})


Passing multiple arguments:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  # You want to do:
  z = [myfunction(x, y, argument1, argument2, mykey=argument3) for (x,y) in mylist]
  # In parallel:
  z = parmap.starmap(myfunction, mylist, argument1, argument2, mykey=argument3)

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


Advanced: Multiple parallel tasks running in parallel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, Task1 uses 5 cores, while Task2 uses 3 cores. Both tasks start
to compute simultaneously, and we print a message as soon as any of the tasks
finishes, retreiving the result.

::

    import parmap
    def task1(item):
        return 2*item

    def task2(item):
        return 2*item + 1

    items1 = range(500000)
    items2 = range(500)

    with parmap.map_async(task1, items1, pm_processes=5) as result1:
        with parmap.map_async(task2, items2, pm_processes=3) as result2:
            data_task1 = None
            data_task2 = None
            task1_working = True
            task2_working = True
            while task1_working or task2_working:
                result1.wait(0.1)
                if task1_working and result1.ready():
                    print("Task 1 has finished!")
                    data_task1 = result1.get()
                    task1_working = False
                result2.wait(0.1)
                if task2_working and result2.ready():
                    print("Task 2 has finished!")
                    data_task2 = result2.get()
                    task2_working = False
    #Further work with data_task1 or data_task2


map and starmap already exist. Why reinvent the wheel?
---------------------------------------------------------

The existing functions have some usability limitations:

-  The built-in python function ``map`` [#builtin-map]_
   is not able to parallelize.
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
-  ``parmap.map(..., ..., pm_parallel=False)`` # disables parallelization
-  ``parmap.map(..., ..., pm_processes=4)`` # use 4 parallel processes
-  ``parmap.map(..., ..., pm_pbar=True)`` # show a progress bar (requires tqdm)
-  ``parmap.map(..., ..., pm_pool=multiprocessing.Pool())`` # use an existing
   pool, in this case parmap will not close the pool.
-  ``parmap.map(..., ..., pm_chunksize=3)`` # size of chunks (see
   multiprocessing.Pool().map)

Limitations:
-------------

``parmap.map()`` and ``parmap.starmap()`` (and their async versions) have their own 
arguments (``pm_parallel``, ``pm_pbar``...). Those arguments are never passed
to the underlying function. In the following example, ``myfun`` will receive 
``myargument``, but not ``pm_parallel``. Do not write functions that require
keyword arguments starting with ``pm_``, as ``parmap`` may need them in the future.

::

    parmap.map(myfun, mylist, pm_parallel=True, myargument=False)

Additionally, there are other keyword arguments that should be avoided in the
functions you write, because of parmap backwards compatibility reasons. The list
of conflicting arguments is: ``parallel``, ``chunksize``, ``pool``,
``processes``, ``callback``, ``error_callback`` and ``parmap_progress``.



Acknowledgments:
----------------

This package started after `this question <https://stackoverflow.com/q/5442910/446149>`__, 
when I offered this `answer <http://stackoverflow.com/a/21292849/446149>`__, 
taking the suggestions of J.F. Sebastian for his `answer <http://stackoverflow.com/a/5443941/446149>`__

Known works using parmap
---------------------------

- Davide Gerosa, Michael Kesden, "PRECESSION. Dynamics of spinning black-hole
  binaries with python." `arXiv:1605.01067 <https://arxiv.org/abs/1605.01067>`__, 2016
- Thibault de Boissiere, `Implementation of Deep learning papers <https://github.com/tdeboissiere/DeepLearningImplementations>`__, 2017
    - Wasserstein Generative Adversarial Networks `arXiv:1701.07875 <https://arxiv.org/abs/1701.07875>`__
    - pix2pix `arXiv:1611.07004 <https://arxiv.org/abs/1611.07004>`__
    - Improved Techniques for Training Generative Adversarial Networks `arXiv:1606.03498 <https://arxiv.org/abs/1606.03498>`__
    - Colorful Image Colorization `arXiv:1603.08511 <https://arxiv.org/abs/1603.08511>`__
    - Deep Feature Interpolation for Image Content Changes `arXiv:1611.05507 <https://arxiv.org/abs/1611.05507>`__
    - InfoGAN `arXiv:1606.03657 <https://arxiv.org/abs/1606.03657>`__
- Geoscience Australia, `SIFRA, a System for Infrastructure Facility Resilience Analysis <https://github.com/GeoscienceAustralia/sifra>`__, 2017
- André F. Rendeiro, Christian Schmidl, Jonathan C. Strefford, Renata Walewska, Zadie Davis, Matthias Farlik, David Oscier, Christoph Bock "Chromatin accessibility maps of chronic lymphocytic leukemia identify subtype-specific epigenome signatures and transcription regulatory networks" Nat. Commun. 7:11938 doi: 10.1038/ncomms11938 (2016). `Paper <https://doi.org/10.5281/zenodo.231352>`__, `Code <https://github.com/epigen/cll-chromatin>`__


References
-----------

.. [#builtin-map] http://docs.python.org/dev/library/functions.html#map
.. [#multiproc-starmap] http://docs.python.org/dev/library/multiprocessing.html#multiprocessing.pool.Pool.starmap
.. [#multiproc-map] http://docs.python.org/dev/library/multiprocessing.html#multiprocessing.pool.Pool.map
.. [#itertools-repeat] http://docs.python.org/dev/library/itertools.html#itertools.repeat

