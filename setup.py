#!/usr/bin/env python
# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import re
from setuptools import setup, find_packages


def get_requirements(path):

    setuppy_format = \
        'https://github.com/{user}/{repo}/tarball/master#egg={egg}'

    setuppy_pattern = \
        r'github.com/(?P<user>[^/.]+)/(?P<repo>[^.]+).git#egg=(?P<egg>.+)'

    dep_links = []
    install_requires = []
    import os
    print(os.getcwd())
    print(path)
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

setup(name='f8dff',
      version='1.0',
      description='fixtures for kobo xlsform tools',
      author='Alex Dorey',
      author_email='alex.dorey@kobotoolbox.org',
      url='https://github.com/kobotoolbox/f8dff/',
      packages=find_packages(),
      install_requires=requirements,
      extras_require={
          'dev': dev_requirements
      }
      )
