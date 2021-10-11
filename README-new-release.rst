How to make a new release
==========================

Version numbering
--------------------
parmap version numbering is borrowed from [#rpackages-release]_.

parmap versions use the following version numbering:
:code:`MAJOR.MINOR.PATCH.DEVELOPMENT`.

- :code:`MAJOR`, :code:`MINOR` and :code:`PATCH` follow the semantic
  versioning of libraries rules [#semver]_:

  - :code:`MAJOR` will only change when there is an incompatible API change.
  - :code:`MINOR` will increase when functionality is added in a
    backwards-compatible way
  - :code:`PATCH` will change for backwards-compatible bug fixes.

- :code:`DEVELOPMENT` is only used in the git repository and is removed before
  official releases.

Creating a new release
------------------------

This is a list of things to do before a release:

- Review the ChangeLog file and add items if necessary.

- Bump the version in :code:`setup.cfg` to a valid release version (without
  :code:`DEVELOPMENT`). Update the version and release in :code:`docs/conf.py` and in
  the Changelog.

- Build the source distribution and the binary wheel

.. code:: bash

    # pip3 install --user -U "pip>=1.4" "setuptools>=0.9" "wheel>=0.21" "twine"
    python3 setup.py sdist bdist_wheel

- Check that there are no missing files in :code:`dist/parmap-x.y.z.tar.gz` and
  on :code:`dist/parmap-x.y.z-py2.py3-none-any.whl`.

- Check that the restructured text is valid with

.. code:: bash

    twine check dist/parmap-[VERSION].tar.gz 

- Commit.

- Tag the release :code:`git tag v#.#.#`.

- Push the release to :code:`origin` [#origin]_: :code:`git push origin --tags`.

- Check that the testsuite [#gh-actions]_ and the documentation [#readthedocs]_
  are updated properly.

- Upload to pypi: :code:`twine upload dist/parmap-#.#.#*`

- Upload to conda-forge:
    * git clone git@github.com:zeehio/parmap-feedstock.git
    * cd parmap-feedstock
    * git remote add conda-forge https://github.com/conda-forge/parmap-feedstock
    * git pull conda-forge master
    * git checkout -b parmap-new-upstream-v#.#.#
    * Edit recipe/meta.yaml
        + Change the version at the top and the sha256 hash (from
          https://pypi.org/project/parmap/#files)
    * git commit, git push
    * Visit https://github.com/conda-forge/parmap-feedstock and create a PR. Follow all
      checks and rules and merge it.
    * Wait for conda continuous integration to finish. Check that the new parmap is at https://anaconda.org/conda-forge/parmap/files

- Bump the version in :code:`setup.cfg` to a valid development version 
  (appending :code:`.9000`). Update the version and release in
  :code:`docs/conf.py`. Commit and push.

References
-----------

.. [#rpackages-release] http://r-pkgs.had.co.nz/release.html
.. [#semver] http://semver.org
.. [#origin] https://github.com/zeehio/parmap
.. [#gh-actions] https://github.com/zeehio/parmap/actions
.. [#readthedocs] https://parmap.readthedocs.org/

