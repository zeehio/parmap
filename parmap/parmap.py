#!/usr/bin/env python
#   Copyright 2014-2026 Sergio Oller <sergioller@gmail.com>
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

import inspect
import multiprocessing
import typing as T
import warnings
from functools import partial
from itertools import repeat
from multiprocessing.pool import AsyncResult

try:
    import tqdm.auto as tqdm  # type: ignore

    HAVE_TQDM = True
except ImportError:
    HAVE_TQDM = False


def _func_star_single(func_item_args):
    """Equivalent to:
    func = func_item_args[0]
    item = func_item_args[1]
    args = func_item_args[2]
    kwargs = func_item_args[3]
    return func(item, args[0], args[1], ..., **kwargs)
    """
    return func_item_args[0](
        *[func_item_args[1]] + func_item_args[2], **func_item_args[3]
    )


def _func_star_many(func_items_args):
    """Equivalent to:
    func = func_items_args[0]
    items = func_items_args[1]
    args = func_items_args[2]
    kwargs = func_items_args[3]
    return func(items[0], items[1], ..., args[0], args[1], ..., **kwargs)
    """
    return func_items_args[0](
        *list(func_items_args[1]) + func_items_args[2], **func_items_args[3]
    )


def _create_pool(kwargs):
    parallel: bool = kwargs.pop("pm_parallel", True)
    pool: T.Optional[multiprocessing.Pool] = kwargs.pop("pm_pool", None)
    close_pool = False
    processes: T.Optional[int] = kwargs.pop("pm_processes", None)
    # Initialize pool if parallel:
    if parallel and pool is None:
        try:
            pool = multiprocessing.Pool(processes=processes)
            close_pool = True
        except Exception as exc:  # Disable parallel on error:
            warnings.warn(str(exc))
            parallel = False
    return parallel, pool, close_pool


def _do_pbar(async_result, num_tasks, chunksize, refresh_time, pbar_wrapper):
    remaining = num_tasks
    # tqdm provides a progress bar.
    # the pbar needs to be updated with the increment on each
    # iteration.
    with pbar_wrapper(total=num_tasks) as pbar:
        while True:
            if async_result.ready():
                pbar.update(remaining)
                break
            try:
                remaining_now = async_result._number_left * chunksize
                done_now = remaining - remaining_now
                remaining = remaining_now
            except AttributeError:
                # _number_left is a private multiprocessing attribute that
                # may not be present on all AsyncResult-like objects.
                break
            if done_now > 0:
                pbar.update(done_now)
            async_result.wait(refresh_time)  # update every two seconds


def _get_default_chunksize(chunksize, pool, num_tasks):
    # default from multiprocessing
    # https://github.com/python/cpython/blob/master/Lib/multiprocessing/pool.py
    if chunksize is None:
        num_workers = len(pool._pool)
        if num_workers == 0:
            return 1
        chunksize, extra = divmod(num_tasks, num_workers * 4)
        if extra:
            chunksize += 1
    return chunksize


def _prepare_pbar_wrapper(progress):
    has_pbar = False
    wrapper = None
    if progress is True and HAVE_TQDM:
        has_pbar = True
        wrapper = tqdm.tqdm
    elif isinstance(progress, dict) and HAVE_TQDM:
        has_pbar = True
        wrapper = partial(tqdm.tqdm, **progress)
    elif callable(progress):
        has_pbar = True
        wrapper = progress
    return (has_pbar, wrapper)


def _serial_map_or_starmap(
    function, iterable, args, kwargs, pbar_wrapper, map_or_starmap
):
    if pbar_wrapper is not None:
        iterable = pbar_wrapper(iterable)
    if map_or_starmap == "map":
        output = [function(*([item] + list(args)), **kwargs) for item in iterable]
    elif map_or_starmap == "starmap":
        output = [function(*(list(item) + list(args)), **kwargs) for item in iterable]
    else:
        raise AssertionError(
            "Internal parmap error: Invalid map_or_starmap." + " This should not happen"
        )
    return output


def _get_helper_func(map_or_starmap):
    if map_or_starmap == "map":
        func_star = _func_star_single
    elif map_or_starmap == "starmap":
        func_star = _func_star_many
    else:
        raise AssertionError(
            "Internal parmap error: Invalid map_or_starmap." + " This should not happen"
        )
    return func_star


def _deprecated_kwargs(kwargs, arg_newarg):
    """arg_newarg is a list of tuples, where each tuple has a pair of strings.
    ('old_arg', 'new_arg')
    A DeprecationWarning is raised for the arguments that need to be
    replaced.
    """
    warn_for = []
    for (arg, new_kw) in arg_newarg:
        if arg in kwargs.keys():
            val = kwargs.pop(arg)
            kwargs[new_kw] = val
            warn_for.append((arg, new_kw))
    if len(warn_for) > 0:
        if len(warn_for) == 1:
            warnings.warn(
                "Argument '{}' is deprecated. Use {} instead".format(
                    warn_for[0][0], warn_for[0][1]
                ),
                DeprecationWarning,
                stacklevel=4,
            )
        else:
            args = ", ".join([x[0] for x in warn_for])
            repl = ", ".join([x[1] for x in warn_for])
            warnings.warn(
                "Arguments '{}' are deprecated. Use '{}' instead respectively".format(
                    args, repl
                ),
                DeprecationWarning,
                stacklevel=4,
            )
    return kwargs


# Keyword arguments reserved by parmap for its own use. If the mapped
# function's own signature declares a parameter with one of these names,
# parmap will consume the caller's value for itself and the function will
# never see it (see _warn_reserved_kwarg_collisions).
_RESERVED_KWARGS_MAP = (
    "pm_parallel",
    "pm_chunksize",
    "pm_pool",
    "pm_processes",
    "pm_pbar",
    "parallel",
    "chunksize",
    "pool",
    "processes",
    "parmap_progress",
)
_RESERVED_KWARGS_ASYNC = (
    "pm_parallel",
    "pm_chunksize",
    "pm_pool",
    "pm_processes",
    "pm_callback",
    "pm_error_callback",
    "parallel",
    "chunksize",
    "pool",
    "processes",
    "callback",
    "error_callback",
)


def _warn_reserved_kwarg_collisions(function, kwargs, reserved_names):
    """Warn if `function`'s own signature declares a parameter name that
    the caller also passed as one of parmap's reserved keyword arguments.
    parmap always consumes those itself, so `function` will not receive
    the value the caller most likely intended for it.
    """
    try:
        parameters = inspect.signature(function).parameters
    except (TypeError, ValueError):
        # function does not support introspection (e.g. some builtins);
        # nothing we can check.
        return
    colliding = [name for name in reserved_names if name in kwargs and name in parameters]
    if colliding:
        warnings.warn(
            "The argument(s) '{}' are reserved for parmap and will not be "
            "passed to {!r}, even though its signature declares a "
            "parameter with that name. Rename the parameter in your "
            "function, or the keyword argument in your call, to avoid "
            "this collision.".format(", ".join(colliding), function),
            UserWarning,
            stacklevel=4,
        )


def _map_or_starmap(function, iterable, args, kwargs, map_or_starmap):
    """
    Shared function between parmap.map and parmap.starmap.
    Refer to those functions for details.
    """
    _warn_reserved_kwarg_collisions(function, kwargs, _RESERVED_KWARGS_MAP)
    arg_newarg = (
        ("parallel", "pm_parallel"),
        ("chunksize", "pm_chunksize"),
        ("pool", "pm_pool"),
        ("processes", "pm_processes"),
        ("parmap_progress", "pm_pbar"),
    )
    kwargs = _deprecated_kwargs(kwargs, arg_newarg)
    chunksize = kwargs.pop("pm_chunksize", None)
    progress = kwargs.pop("pm_pbar", False)
    (has_pbar, pbar_wrapper) = _prepare_pbar_wrapper(progress)
    parallel, pool, close_pool = _create_pool(kwargs)
    # Handle case: Execute sequentially:
    if not parallel:
        return _serial_map_or_starmap(
            function, iterable, args, kwargs, pbar_wrapper, map_or_starmap
        )
    func_star = _get_helper_func(map_or_starmap)
    # Handle case: Without showing progress bar
    if not has_pbar:
        try:
            result = pool.map_async(
                func_star,
                zip(repeat(function), iterable, repeat(list(args)), repeat(kwargs)),
                chunksize,
            )
            output = result.get()
        except:
            if close_pool:
                pool.terminate()
            raise
        else:
            if close_pool:
                pool.close()
                pool.join()
        return output
    # Handle case: Show progress bar:
    try:
        num_tasks = len(iterable)
        # get a chunksize (as multiprocessing does):
        chunksize = _get_default_chunksize(chunksize, pool, num_tasks)
        # use map_async to get progress information
        result = pool.map_async(
            func_star,
            zip(repeat(function), iterable, repeat(list(args)), repeat(kwargs)),
            chunksize,
        )
    except:
        if close_pool:
            pool.terminate()
        raise
    else:
        if close_pool:
            pool.close()
    # Progress bar:
    try:
        _do_pbar(
            result, num_tasks, chunksize, refresh_time=2, pbar_wrapper=pbar_wrapper
        )
    finally:
        output = result.get()
        if close_pool:
            pool.join()
    return output


def map(function, iterable, *args, **kwargs):
    """This function is equivalent to:
     >>> [function(x, args[0], args[1],...) for x in iterable]

    :param pm_parallel: Force parallelization on/off
    :type pm_parallel: bool
    :param pm_chunksize: see  :py:class:`multiprocessing.pool.Pool`
    :type pm_chunksize: int
    :param pm_pool: Pass an existing pool
    :type pm_pool: multiprocessing.pool.Pool
    :param pm_processes: Number of processes to use in the pool. See
      :py:class:`multiprocessing.pool.Pool`
    :type pm_processes: int
    :param pm_pbar: Show progress bar with optional information.

         * If it is a `boolean`, whether to show or not the progress bar.
         * If it is a `dictionary`, these are options passed to `tqdm.tqdm()`.
         * If it is a `callable`, the callable is a function compatible with `tqdm.tqdm()`.
           If you want to pass additional options to your callable, consider using :py:func:`functools.partial`::

             from functools import partial
             from tqdm_loggable.auto import tqdm
             parmap.map(print, range(10), pm_pbar = partial(tqdm, desc = "example"))

    :type pm_pbar: bool, dict or callable
    """
    return _map_or_starmap(function, iterable, args, kwargs, "map")


def starmap(function, iterables, *args, **kwargs):
    """Equivalent to:
         >>> return ([function(x1,x2,x3,..., args[0], args[1],...) for
         >>>         (x1,x2,x3...) in iterable])

    :param pm_parallel: Force parallelization on/off
    :type pm_parallel: bool
    :param pm_chunksize: see  :py:class:`multiprocessing.pool.Pool`
    :type pm_chunksize: int
    :param pm_pool: Pass an existing pool
    :type pm_pool: multiprocessing.pool.Pool
    :param pm_processes: Number of processes to use in the pool. See
                      :py:class:`multiprocessing.pool.Pool`
    :type pm_processes: int
    :param pm_pbar: Show progress bar with optional information.

         * If it is a `boolean`, whether to show or not the progress bar.
         * If it is a `dictionary`, these are options passed to `tqdm.tqdm()`.
         * If it is a `callable`, the callable is a function compatible with `tqdm.tqdm()`.
           If you want to pass additional options to your callable, consider using :py:func:`functools.partial`::

             from functools import partial
             from tqdm_loggable.auto import tqdm
             parmap.map(print, range(10), pm_pbar = partial(tqdm, desc = "example"))

    :type pm_pbar: bool, dict or callable
    """
    return _map_or_starmap(function, iterables, args, kwargs, "starmap")


class _DummyAsyncResult(AsyncResult):
    """AsyncResult compatible class, for when parallelization is disabled
    It is a dummy class.
    """

    def __init__(self, values):
        self._values = values

    @property
    def _number_left(self):
        return 0

    def get(self, timeout=None):
        return self._values

    def wait(self, timeout=None):
        pass

    def ready(self):
        return True

    def successful(self):
        # The exception would have been raised in the computation of result
        return True

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass


class _ParallelAsyncResult(AsyncResult):
    """Like the AsyncResult, but it will close the pool when we leave the
    ``with`` block or when we check if it is ready.
    """

    def __init__(self, result, pool=None):
        self._result = result
        self._pool = pool

    @property
    def _number_left(self):
        return self._result._number_left

    def get(self, timeout=None):
        try:
            return self._result.get(timeout)
        finally:
            # Only join if the underlying result is actually done: a
            # TimeoutError means the task is still running, and joining
            # would block until it finishes instead of letting the
            # caller retry get() later.
            if self._result.ready():
                self.join()

    def wait(self, timeout=None):
        return self._result.wait(timeout)

    def ready(self):
        is_ready = self._result.ready()
        if is_ready:
            self.join()
        return is_ready

    def successful(self):
        return self._result.successful()

    def __enter__(self):
        return self

    def join(self):
        if self._pool is not None:
            self._pool.join()
            self._pool = None

    def terminate(self):
        if self._pool is not None:
            self._pool.terminate()
            self._pool = None

    def __exit__(self, type, value, traceback):
        self.terminate()


def _map_or_starmap_async(function, iterable, args, kwargs, map_or_starmap):
    """
    Shared function between parmap.map_async and parmap.starmap_async.
    Refer to those functions for details.
    """
    _warn_reserved_kwarg_collisions(function, kwargs, _RESERVED_KWARGS_ASYNC)
    arg_newarg = (
        ("parallel", "pm_parallel"),
        ("chunksize", "pm_chunksize"),
        ("pool", "pm_pool"),
        ("processes", "pm_processes"),
        ("callback", "pm_callback"),
        ("error_callback", "pm_error_callback"),
    )
    kwargs = _deprecated_kwargs(kwargs, arg_newarg)
    chunksize = kwargs.pop("pm_chunksize", None)
    callback = kwargs.pop("pm_callback", None)
    error_callback = kwargs.pop("pm_error_callback", None)
    parallel, pool, close_pool = _create_pool(kwargs)
    # Map:
    if parallel:
        func_star = _get_helper_func(map_or_starmap)
        try:
            result = pool.map_async(
                func_star,
                zip(repeat(function), iterable, repeat(list(args)), repeat(kwargs)),
                chunksize=chunksize,
                callback=callback,
                error_callback=error_callback,
            )
        except:
            if close_pool:
                pool.terminate()
            raise
        else:
            if close_pool:
                pool.close()
                result = _ParallelAsyncResult(result, pool)
            else:
                result = _ParallelAsyncResult(result)
    else:
        values = _serial_map_or_starmap(
            function, iterable, args, kwargs, None, map_or_starmap
        )
        result = _DummyAsyncResult(values)
    return result


def map_async(function, iterable, *args, **kwargs):
    """This function is the multiprocessing.Pool.map_async version that
    supports multiple arguments.

     >>> [function(x, args[0], args[1],...) for x in iterable]

    :param pm_parallel: Force parallelization on/off. If False, the
                        function won't be asynchronous.
    :type pm_parallel: bool
    :param pm_chunksize: see  :py:class:`multiprocessing.pool.Pool`
    :type pm_chunksize: int
    :param pm_callback: see  :py:class:`multiprocessing.pool.Pool`
    :type pm_callback: function
    :param pm_error_callback: (not on python 2) see
        :py:class:`multiprocessing.pool.Pool`
    :type pm_error_callback: function
    :param pm_pool: Pass an existing pool.
    :type pm_pool: multiprocessing.pool.Pool
    :param pm_processes: Number of processes to use in the pool. See
      :py:class:`multiprocessing.pool.Pool`
    :type pm_processes: int
    """
    return _map_or_starmap_async(function, iterable, args, kwargs, "map")


def starmap_async(function, iterables, *args, **kwargs):
    """This function is the multiprocessing.Pool.starmap_async version that
    supports multiple arguments.

         >>> return ([function(x1,x2,x3,..., args[0], args[1],...) for
         >>>         (x1,x2,x3...) in iterable])

    :param pm_parallel: Force parallelization on/off. If False, the
                        function won't be asynchronous.
    :type pm_parallel: bool
    :param pm_chunksize: see  :py:class:`multiprocessing.pool.Pool`
    :type pm_chunksize: int
    :param pm_callback: see  :py:class:`multiprocessing.pool.Pool`
    :type pm_callback: function
    :param pm_error_callback: see  :py:class:`multiprocessing.pool.Pool`
    :type pm_error_callback: function
    :param pm_pool: Pass an existing pool.
    :type pm_pool: multiprocessing.pool.Pool
    :param pm_processes: Number of processes to use in the pool. See
      :py:class:`multiprocessing.pool.Pool`
    :type pm_processes: int
    """
    return _map_or_starmap_async(function, iterables, args, kwargs, "starmap")
