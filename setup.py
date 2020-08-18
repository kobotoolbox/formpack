#!/usr/bin/env python
# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from setuptools import setup, find_packages
import sys


PYXFORM_COMMIT = 'afb64e2fe1abae4e978a86e8b202a2be1b3eff79'
A1D05EB_COMMIT = '6bb19b4075e1fd1cc14ef90a27e0108c336961f3'
gh_package = '{1}@git+https://github.com/{0}/{1}.git#{2}'

requirements = [
    'begins',
    'jsonschema',
    'lxml',
    'path.py',
    'pyquery',
    # gh_package.format('XLSForm', 'pyxform', PYXFORM_COMMIT),
    # gh_package.format('dorey', 'a1d05eba1', A1D05EB_COMMIT),
    'statistics',
    'XlsxWriter',
    'backports.csv',  # Remove after dropping Python 2 support (and rewrite `imports`)
    'geojson-rewind',
]

dep_links = []


setup(name='formpack',
      version='2.0.1',
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
