pmap
====

This small python module implements two functions: `map` and `starmap`.

## What does pmap offer?

 - Provide an easy to use syntax for both `map` and `starmap`.
 - Parallelize transparently whenever possible.
 - Handle multiple (positional -for now-) arguments as needed.

## Usage:

Here are some examples with some unparallelized code parallelized with pmap:

```python

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
    listz = pmap.starmap(myfunction, zip(listx, listy), param1, param2)
```

## map (and starmap on python 3.3) already exist. Why reinvent the wheel?

Please correct me if I am wrong, but from my point of view, existing functions
have some usability limitations:

 - The built-in python function [`map`](http://docs.python.org/dev/library/functions.html#map) is not able to parallelize.
 - [`multiprocessing.Pool().starmap`](http://docs.python.org/dev/library/multiprocessing.html#multiprocessing.pool.Pool.starmap) is available in python-3.3 and later versions.
 - [`multiprocessing.Pool().map`](http://docs.python.org/dev/library/multiprocessing.html#multiprocessing.pool.Pool.map) does not allow any additional argument to the
   mapped function.
 - `multiprocessing.Pool().starmap` allows passing multiple arguments, but in
   order to pass a constant argument to the mapped function you will need to
   convert it to an iterator using [`itertools.repeat`](http://docs.python.org/2/library/itertools.html#itertools.repeat)`(your_parameter)`

### Additional features in pmap:

 - Create a pool for parallel computation automatically if possible.
 - `pmap.map(..., ..., parallel=False)`  # disables parallelization
 - `pmap.map(..., ..., chunksize=3)`  # size of chunks (see multiprocessing.Pool().map)
 - `pmap.map(..., ..., pool=multiprocessing.Pool())`  # use an existing pool



## To do:

Pull requests and suggestions are welcome.

 - [ ] See if anyone is interested on this
 - [ ] Pass keyword arguments to functions
 - [ ] Make a real module out of this (on pypi, pip install...)?
 - [ ] Improve exception handling
 - [ ] Sphinx documentation?
