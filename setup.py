#!/usr/bin/env python
# coding: utf-8
from setuptools import setup, find_packages

requirements = [
    'begins',
    'jsonschema',
    'lxml',
    'path.py',
    'pyquery',
    'pyxform',
    'statistics',
    'XlsxWriter',
    'geojson-rewind',
]

dep_links = [
]


setup(
    name='formpack',
    version='3.0.0',
    description='Manipulation tools for KoBo forms',
    author='the formpack contributors (https://github.com/kobotoolbox/formpack/graphs/contributors)',
    url='https://github.com/kobotoolbox/formpack/',
    packages=[str(pkg) for pkg in find_packages('src')],
    package_dir={'': 'src'},
    install_requires=requirements,
    dependency_links=dep_links,
    include_package_data=True,
    zip_safe=False,
)
