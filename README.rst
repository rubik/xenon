xenon
=====

.. image:: https://img.shields.io/travis/rubik/xenon/master.svg
    :alt: Travis-CI badge
    :target: https://travis-ci.org/rubik/xenon

.. image:: https://img.shields.io/coveralls/rubik/xenon/master.svg
    :alt: Coveralls badge
    :target: https://coveralls.io/r/rubik/xenon?branch=master

.. image:: https://img.shields.io/pypi/v/xenon.svg
    :alt: PyPI latest version badge
    :target: https://pypi.python.org/pypi/xenon/

.. image:: https://img.shields.io/pypi/format/xenon.svg
    :alt: Download format
    :target: http://pythonwheels.com/

.. image:: https://img.shields.io/pypi/l/xenon.svg
    :alt: Xenon license
    :target: https://pypi.python.org/pypi/xenon/


----

Xenon is a monitoring tool based on `Radon <https://github.com/rubik/radon/>`_.
It monitors your code's complexity.  Ideally, Xenon is run every time you
commit code. Through command line options, you can set various thresholds for
the **complexity** of your code. It will fail (i.e. it will exit with a
non-zero exit code) when any of these requirements is not met.

Installation
------------

With Pip:

.. code-block:: sh

   $ pip install xenon

Or download the source and run the setup file (requires setuptools):

.. code-block:: sh

   $ python setup.py install

Xenon is tested with Python versions **2.7** and **3.6** to **3.12** as well as
**PyPy**.

Usage
-----

Typically you would use Xenon in two scenarios:

1. As a ``git commit`` hook: to make sure that your code never exceeds some
   complexity values.

2. On a **continuous integration** server: as a part of your build, to keep
   under control, as above, your code's complexity. See Xenon's
   `.travis.yml file`_ for an example usage.

The command line
++++++++++++++++

Everything boils down to Xenon's command line usage.
To control which files are analyzed, you use the options ``-e, --exclude`` and
``-i, --ignore``. Both accept a comma-separated list of glob patterns. The
value usually needs quoting at the command line, to prevent the shell from
expanding the pattern (in case there is only one). Every filename is matched
against the *exclude* patterns. Every directory name is matched against the
*ignore* patterns.  If any of the patterns matches, Xenon won't even descend
into them.

The actual threshold values are defined through these options:

* ``-a, --max-average``: Threshold for the *average* complexity (across all the
  codebase).
* ``-m, --max-modules``: Threshold for *modules* complexity.
* ``-b, --max-absolute``: *Absolute* threshold for *block* complexity.


All of these options are inclusive.

An actual example
+++++++++++++++++

.. code-block:: sh

   $ xenon --max-absolute B --max-modules A --max-average A

or, more succinctly:

.. code-block:: sh

   $ xenon -b B -m A -a A

With these options Xenon will exit with a non-zero exit code if any of the
following conditions is met:

* At least one block has a rank higher than ``B`` (i.e. ``C``, ``D``, ``E`` or
  ``F``).
* At least one module has a rank higher than ``A``.
* The average complexity (among all of the analyzed blocks) is ranked with
  ``B`` or higher.

Pre-commit hook
+++++++++++++++

Xenon can be used in combination with `pre-commit <https://pre-commit.com/>`_ as follows:

.. code-block:: yaml

    # monitor code complexity
    - repo: https://github.com/rubik/xenon
      rev: v0.9.0
      hooks:
      - id: xenon
        args: ['--max-absolute=B', '--max-modules=B', '--max-average=A']

Note: due to how options are passed to commands by pre-commit, make sure to
pass values either with an equals sign like in the above example, or by
splitting them as separate list items, e.g. ``['--max-absolute', 'B']``.

Other resources
---------------

For more information regarding cyclomatic complexity and static analysis in
Python, please refer to Radon's documentation, the project on which Xenon is
based on:

* More on cyclomatic complexity:
  http://radon.readthedocs.org/en/latest/intro.html
* More on Radon's ranking:
  http://radon.readthedocs.org/en/latest/commandline.html#the-cc-command


.. _.travis.yml file: https://github.com/rubik/xenon/blob/master/.travis.yml
