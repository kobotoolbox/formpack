# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import importlib
from copy import deepcopy


def build_fixture(modulename):
    fixtures = deepcopy(importlib.import_module('..%s' % modulename, __name__).DATA)

    try:
        title = fixtures.get('title')

        # separate the submissions from the schema
        schemas = [dict(v) for v in fixtures['versions']]
        submissions = []
        for s in schemas:
            _version = s.get('version')
            _version_id_key = s.get('version_id_key', '__version__')
            for _s in s.pop('submissions'):
                _s.update({_version_id_key: _version})
                submissions.append(_s)
        return title, schemas, submissions
    except KeyError:
        # TODO: generalize this ?
        # it's an xml schme json fixture
        return fixtures
