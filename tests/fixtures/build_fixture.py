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
        submissions = []
        for s in schemas:
            _version = s.get('version')
            submissions.append([s.update({'__version__': _version})
                                for s in s.pop('submissions')])
        return title, schemas, submissions
    except KeyError:
        # TODO: generalize this ?
        # it's an xml schme json fixture
        return fixtures
