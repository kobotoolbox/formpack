# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import importlib


def build_fixture(modulename):
    fixtures = importlib.import_module('..%s' % modulename, __name__).DATA

    try:
        title = fixtures.get('title')

        # separate the submissions from the schema
        schemas = [dict(v) for v in fixtures['versions']]
        submissions = [(s.get('version'), s.pop('submissions')) for s in schemas]

        return title, schemas, submissions
    except KeyError:
        # TODO: generalize this ?
        # it's an xml schme json fixture
        return fixtures
