#!/usr/bin/env python
# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import re
import sys
from setuptools import setup, find_packages


def get_requirements(path):

    setuppy_format = \
        'https://github.com/{user}/{repo}/tarball/master#egg={egg}'

    setuppy_pattern = \
        r'github.com/(?P<user>[^/.]+)/(?P<repo>[^.]+).git#egg=(?P<egg>.+)'

    dep_links = []
    install_requires = []
    with open(path) as f:
        for line in f:

            if line.startswith('-e'):
                url_infos = re.search(setuppy_pattern, line).groupdict()
                dep_links.append(setuppy_format.format(**url_infos))
                egg_name = '=='.join(url_infos['egg'].rsplit('-', 1))
                install_requires.append(egg_name)
            else:
                install_requires.append(line.strip())

    return install_requires, dep_links


requirements, dep_links = get_requirements('requirements.txt')
dev_requirements, dev_dep_links = get_requirements('dev-requirements.txt')

if 'develop' in sys.argv:
    requirements += dev_requirements
    dep_links += dev_dep_links

setup(name='formpack',
      version='1.4',
      description='Manipulation tools for kobocat forms',
      author='Alex Dorey',
      author_email='alex.dorey@kobotoolbox.org',
      url='https://github.com/kobotoolbox/formpack/',
      packages=[str(pkg) for pkg in find_packages('src')],
      package_dir={'': b'src'},
      install_requires=requirements,
      include_package_data=True,
      zip_safe=False,
      )
