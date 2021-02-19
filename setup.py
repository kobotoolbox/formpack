#!/usr/bin/env python
# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from setuptools import setup, find_packages
import sys


if sys.version_info[0] == 2:

    requirements = [
        'begins',
        'cyordereddict',
        'jsonschema',
        'lxml',
        'path.py<12',  # Pinned for Python 2 compatibility
        'pyquery',
        'pyxform',
        'statistics',
        'XlsxWriter',
        'backports.csv',  # Remove after dropping Python 2 support (and rewrite `imports`)
        'geojson-rewind==0.1.1+py2.jnm',  # Stop using fork after dropping Python 2 support
    ]

    dep_links = [
        # "Be careful with the version" part of `#egg=project-version`, according to
        # https://setuptools.readthedocs.io/en/latest/setuptools.html#dependencies-that-aren-t-in-pypi.
        # "It should match the one inside the project files," i.e. the `version`
        # argument to `setup()` in `setup.py`. It should also adhere to PEP 440.
        'https://github.com/jnm/geojson-rewind/tarball/master#egg=geojson-rewind-0.1.1+py2.jnm'
    ]

else:

    requirements = [
        'begins',
        'jsonschema',
        'lxml',
        'path.py',
        'pyquery',
        'pyxform',
        'statistics',
        'XlsxWriter',
        'backports.csv',  # Remove after dropping Python 2 support (and rewrite `imports`)
        'geojson-rewind',
    ]

    dep_links = [
    ]


setup(name='formpack',
      version='2.1.0',
      description='Manipulation tools for KoBo forms',
      author='the formpack contributors (https://github.com/kobotoolbox/formpack/graphs/contributors)',
      url='https://github.com/kobotoolbox/formpack/',
      packages=[str(pkg) for pkg in find_packages('src')],
      package_dir={'': str('src')},  # coercing to `str` only necessary for Python 2, see
                                     # https://github.com/sdss/python_template/issues/9
      install_requires=requirements,
      dependency_links=dep_links,
      include_package_data=True,
      zip_safe=False,
      )
