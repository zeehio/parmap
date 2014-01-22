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
Module name: pmap
Author: Sergio Oller <soller@el.ub.edu>
Date: 2014-01-22
Version: 1.0
Tested on: python-2.7.3 and python-3.2.3
Description: Implement map and starmap functions. Both implementations
 will parallelize if possible using multiprocess.Pool.
 Additionally bot functions allow additional parameters to be passed 
 to the called function. See Usage.
Usage:
    import pmap
    # You want to do:
    y = [myfunction(x, argument1, argument2) for x in mylist]
    # In parallel:
    y = pmap.map(myfunction, mylist, argument1, argument2)

    # You want to do:
    z = [myfunction(x, y, argument1, argument2) for (x,y) in mylist]
    # In parallel:
    z = pmap.starmap(myfunction, mylist, argument1, argument2)

    # Yoy want to do:
    listx = [1, 2, 3, 4, 5, 6]
    listy = [2, 3, 4, 5, 6, 7]
    param = 3.14
    param2 = 42
    listz = []
    for x in listx:
        for y in listy:
            listz.append(myfunction(x, y, param1, param2))
    # In parallel:
    listz = pmap.starmap(myfunction, zip(listx,listy), param1, param2)

"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

try:
    from itertools import izip
except ImportError:  # Python 3 built-in zip already returns iterable
    izip = zip

from itertools import repeat


try:
    import multiprocessing
    HAVE_PARALLEL = True
except ImportError:
    HAVE_PARALLEL = False

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



def map(function, iterable, *args, **kwargs):
    """ 
    Equivalent to:
    return [function(x, args[0], args[1],...) for x in iterable]
    Parallellization is enabled if it is available via multiprocessing,
    although it can be switched off by using parallel=False on the map
    call.
    """
    parallel = kwargs.get("parallel", None)
    chunksize = kwargs.get("chunksize", None)
    pool = kwargs.get("pool", None)
    # Check if parallel is inconsistent with HAVE_PARALLEL:
    if HAVE_PARALLEL == False and parallel == True:
        print("W: Parallelization is disabled because",
              "multiprocessing is missing")
        parallel = False
    # Set default value for parallel:
    if parallel is None:
        parallel = HAVE_PARALLEL
    # Initialize pool if parallel:
    if parallel and pool is None:
        try:
            pool = multiprocessing.Pool()
        except AssertionError:  # Disable parallel on error:
            print("W: Could not create multiprocessing.Pool.",
                  "Parallel disabled")
            parallel = False
    # Map:
    if parallel:
        output = pool.map(_func_star_single,
                          izip(repeat(function), iterable,
                               repeat(list(args))),
                          chunksize)
        pool.close()
        pool.join()
    else:
        output = []
        for item in iterable:
            output.append(function(*([item] + list(args))))
    return output

def starmap(function, iterables, *args, **kwargs):
    """ Equivalent to:
        return [function(x1,x2,x3,..., args[0], args[1],...) for \
            (x1,x2,x3...) in iterable]
        Only parallellization is enabled if possible.   
    """
    parallel = kwargs.get("parallel", None)
    chunksize = kwargs.get("chunksize", None)
    pool = kwargs.get("pool", None)
    # Check if parallel is inconsistent with HAVE_PARALLEL:
    if HAVE_PARALLEL == False and parallel == True:
        print("W: Parallelization is disabled because",
              "multiprocessing is missing")
        parallel = False
    # Set default value for parallel:
    if parallel is None:
        parallel = HAVE_PARALLEL
    # Initialize pool if parallel:
    if parallel and pool is None:
        try:
            pool = multiprocessing.Pool()
        except AssertionError:  # Disable parallel on error:
            print("W: Could not create multiprocessing.Pool.",
                  "Parallel disabled")
            parallel = False
    # Map:
    if parallel:
        output = pool.map(_func_star_many,
                          izip(repeat(function),
                               iterables, repeat(list(args))),
                          chunksize)
        pool.close()
        pool.join()
    else:
        output = []
        for item in iterables:
            output.append(function(*(list(item) + list(args))))
    return output


if __name__ == "__main__":
    multiprocessing.freeze_support()
    def _func(*aaa):
        """ Prints and returns the inputs. Trivial example."""
        print(aaa)
        return aaa
    print("Example1: Begins")
    ITEMS = [1, 2, 3, 4]
    OUT = map(_func, ITEMS, 5, 6, 7, 8, parallel=False)
    print("Using parallel:")
    OUT_P = map(_func, ITEMS, 5, 6, 7, 8, parallel=True)
    if OUT != OUT_P:
        print("Example1: Failed")
    else:
        print("Example1: Success")
    print("Example2: Begins")
    ITEMS = [(1, 'a'), (2, 'b'), (3, 'c')]
    OUT = starmap(_func, ITEMS, 5, 6, 7, 8, parallel=False)
    print("Using parallel")
    OUT_P = starmap(_func, ITEMS, 5, 6, 7, 8, parallel=True)
    if OUT != OUT_P:
        print("Example2: Failed")
    else:
        print("Example2: Success")

