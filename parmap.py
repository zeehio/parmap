#!/usr/bin/env python
#   Copyright 2014 Sergio Oller <sergioller@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
This module implements map and starmap functions (see python standard
library to learn about them).

The implementations provided in this module allow providing additional
arguments to the mapped functions. Additionally they will initialize
the pool and close it automatically by default if possible.

The easiest way to learn is by reading the following examples.

===========
Examples
===========

Map example
===========
You want to do:
    >>> y1 = [myfunction(x, argument1, argument2) for x in mylist]
In parallel:
    >>> y2 = parmap.map(myfunction, mylist, argument1, argument2)
Check both results:
    >>> assert y1 == y2

Starmap example
================

You want to do:
    >>> z1 = [myfunction(x, y, argument1, argument2) for (x,y) in mylist]
In parallel:
    >>> z2 = parmap.starmap(myfunction, mylist, argument1, argument2)
Check both results:
    >>> assert z1 == z2


You want to do:
    >>> listx = [1, 2, 3, 4, 5, 6]
    >>> listy = [2, 3, 4, 5, 6, 7]
    >>> a = 3.14
    >>> b = 42
    >>> listz1 = []
    >>> for x in listx:
    >>>     for y in listy:
    >>>         listz1.append(myfunction(x, y, a, b))
In parallel:
    >>> from itertools import product
    >>> listz2 = parmap.starmap(myfunction, product(listx, listy), a, b)
Check both results:
    >>> assert listz1 == listz2

========
Members
========
"""
# The original idea for this implementation was given by J.F. Sebastian
# at  http://stackoverflow.com/a/5443941/446149


from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import warnings
import sys

try:
    from itertools import izip
except ImportError:  # Python 3 built-in zip already returns iterable
    izip = zip

from itertools import repeat
import multiprocessing

try:
    import tqdm
    HAVE_TQDM = True
except ImportError:
    HAVE_TQDM = False

def _func_star_single(func_item_args):
    """Equivalent to:
       func = func_item_args[0]
       item = func_item_args[1]
       args = func_item_args[2:]
       return func(item,args[0],args[1],...)
    """
    return func_item_args[0](*[func_item_args[1]] + func_item_args[2])


def _func_star_many(func_items_args):
    """Equivalent to:
       func = func_item_args[0]
       items = func_item_args[1]
       args = func_item_args[2:]
       return func(items[0],items[1],...,args[0],args[1],...)
    """
    return func_items_args[0](*list(func_items_args[1]) + func_items_args[2])


def _create_pool(kwargs):
    parallel = kwargs.get("parallel", True)
    pool = kwargs.get("pool", None)
    close_pool = False
    processes = kwargs.get("processes", None)
    # Initialize pool if parallel:
    if parallel and pool is None:
        try:
            pool = multiprocessing.Pool(processes=processes)
            close_pool = True
        except Exception as exc:  # Disable parallel on error:
            warnings.warn(str(exc))
            parallel = False
    return parallel, pool, close_pool


def map(function, iterable, *args, **kwargs):
    """This function is equivalent to:
        >>> [function(x, args[0], args[1],...) for x in iterable]

       :param parallel: Force parallelization on/off
       :type parallel: bool
       :param chunksize: see  :py:class:`multiprocessing.pool.Pool`
       :type chunksize: int
       :param pool: Pass an existing pool
       :type pool: multiprocessing.pool.Pool
       :param processes: Number of processes to use in the pool. See
         :py:class:`multiprocessing.pool.Pool`
       :type processes: int
       :param parmap_progress: Show progress bar
       :type parmap_progress: bool
    """
    chunksize = kwargs.get("chunksize", None)
    progress = kwargs.get("parmap_progress", False)
    progress = progress and HAVE_TQDM
    parallel, pool, close_pool = _create_pool(kwargs)
    # Map:
    if parallel:
        try:
            if progress and close_pool:
                num_tasks = len(iterable)
                # chunksize default from multiprocessing:
                if chunksize is None:
                    chunksize, extra = divmod(num_tasks, len(pool._pool) * 4)
                    if extra:
                        chunksize += 1
                # use map_async to get progress information
                result = pool.map_async(_func_star_single,
                                        izip(repeat(function), iterable,
                                             repeat(list(args))),
                                        chunksize)
                pool.close()
                # Progress bar stuff:
                try:
                    remaining = num_tasks
                    # tqdm provides a progress bar.
                    # the pbar needs to be updated with the increment on each
                    # iteration.
                    with tqdm.tqdm(total=num_tasks) as pbar:
                        while True:
                            if (result.ready()):
                                pbar.update(remaining)
                                break
                            try:
                                remaining_now = result._number_left*chunksize
                                done_now = remaining - remaining_now
                                remaining = remaining_now
                            except:
                                break
                            if done_now > 0:
                                pbar.update(done_now)
                            result.wait(2) # update every two seconds
                finally:
                    output = result.get()
            else:
                output = pool.map(_func_star_single,
                                  izip(repeat(function), iterable,
                                       repeat(list(args))),
                                  chunksize)
        finally:
            if close_pool:
                if not progress:
                    pool.close()
                pool.join()
    else:
        output = [function(*([item] + list(args))) for item in iterable]
    return output

def map_async(function, iterable, *args, **kwargs):
    """This function is the multiprocessing.Pool.map_async version that
       supports multiple arguments.
       
        >>> [function(x, args[0], args[1],...) for x in iterable]

       :param parallel: Force parallelization on/off
       :type parallel: bool
       :param chunksize: see  :py:class:`multiprocessing.pool.Pool`
       :type chunksize: int
       :param callback: see  :py:class:`multiprocessing.pool.Pool`
       :type callback: function
       :param error_callback: (on python 3) see  :py:class:`multiprocessing.pool.Pool`
       :type error_callback: function
       :param pool: Pass an existing pool.
       :type pool: multiprocessing.pool.Pool
       :param processes: Number of processes to use in the pool. See
         :py:class:`multiprocessing.pool.Pool`
       :type processes: int
    """
    chunksize = kwargs.get("chunksize", None)
    callback = kwargs.get("callback", None)
    error_callback = kwargs.get("error_callback", None)
    parallel, pool, close_pool = _create_pool(kwargs)
    # Map:
    if parallel:
        try:
            if sys.version_info[0] == 2:  # python2 does not support error_callback
                output = pool.map_async(_func_star_single,
                                        izip(repeat(function), iterable,
                                             repeat(list(args))),
                                        chunksize, callback)
            else:
                output = pool.map_async(_func_star_single,
                                        izip(repeat(function), iterable,
                                             repeat(list(args))),
                                        chunksize, callback, error_callback)
        finally:
            if close_pool:
                pool.close()
                pool.join()
    else:
        output = [function(*([item] + list(args))) for item in iterable]
    return output

def starmap(function, iterables, *args, **kwargs):
    """ Equivalent to:
            >>> return ([function(x1,x2,x3,..., args[0], args[1],...) for
            >>>         (x1,x2,x3...) in iterable])

       :param parallel: Force parallelization on/off
       :type parallel: bool
       :param chunksize: see  :py:class:`multiprocessing.pool.Pool`
       :type chunksize: int
       :param pool: Pass an existing pool
       :type pool: multiprocessing.pool.Pool
       :param processes: Number of processes to use in the pool. See
                         :py:class:`multiprocessing.pool.Pool`
       :type processes: int
    """
    chunksize = kwargs.get("chunksize", None)
    parallel, pool, close_pool = _create_pool(kwargs)
    # Map:
    if parallel:
        try:
            output = pool.map(_func_star_many,
                              izip(repeat(function),
                                   iterables, repeat(list(args))),
                              chunksize)
        finally:
            if close_pool:
                pool.close()
                pool.join()
    else:
        output = [function(*(list(item) + list(args))) for item in iterables]
    return output

def starmap_async(function, iterables, *args, **kwargs):
    """This function is the multiprocessing.Pool.starmap_async version that
       supports multiple arguments.

            >>> return ([function(x1,x2,x3,..., args[0], args[1],...) for
            >>>         (x1,x2,x3...) in iterable])

       :param parallel: Force parallelization on/off
       :type parallel: bool
       :param chunksize: see  :py:class:`multiprocessing.pool.Pool`
       :type chunksize: int
       :param callback: see  :py:class:`multiprocessing.pool.Pool`
       :type callback: function
       :param error_callback: see  :py:class:`multiprocessing.pool.Pool`
       :type error_callback: function
       :param pool: Pass an existing pool.
       :type pool: multiprocessing.pool.Pool
       :param processes: Number of processes to use in the pool. See
         :py:class:`multiprocessing.pool.Pool`
       :type processes: int
    """
    chunksize = kwargs.get("chunksize", None)
    callback = kwargs.get("callback", None)
    error_callback = kwargs.get("error_callback", None)
    parallel, pool, close_pool = _create_pool(kwargs)
    # Map:
    if parallel:
        try:
            if sys.version_info[0] == 2:
                output = pool.map_async(_func_star_many,
                                        izip(repeat(function),
                                        iterables, repeat(list(args))),
                                        chunksize)
            else:
                output = pool.map_async(_func_star_many,
                                        izip(repeat(function),
                                        iterables, repeat(list(args))),
                                        chunksize, error_callback)
        finally:
            if close_pool:
                pool.close()
                pool.join()
    else:
        output = [function(*(list(item) + list(args))) for item in iterables]
    return output
