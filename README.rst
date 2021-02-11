formpack: machinery to build and export reports for xlsform data
================================================================

.. image:: https://github.com/kobotoolbox/formpack/workflows/pytest/badge.svg
    :target: https://github.com/kobotoolbox/formpack/actions?query=workflow%3Apytest
.. image:: https://coveralls.io/repos/github/kobotoolbox/formpack/badge.svg?branch=master
    :target: https://coveralls.io/github/kobotoolbox/formpack?branch=master

Setup
-----

Install::

    python setup.py install

Develop::

    # Create and activate a new virtualenv, then:
    pip install -r dev-requirements.txt

Test::

    # Within a development environment, as described above:
    pytest

Command line methods::

    python -m formpack xls example.xlsx # convert xlsx file to json
