# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import os
import importlib
from copy import deepcopy


def build_fixture(modulename, data_variable_name="DATA"):
    fixtures = deepcopy(getattr(importlib.import_module('..%s' % modulename, __name__), data_variable_name))

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

def open_fixture_file(modulename, filename, *args, **kwargs):
    fixture_dir = os.path.dirname(
        os.path.abspath(
            importlib.import_module('..%s' % modulename, __name__).__file__
    ))
    return open(os.path.join(fixture_dir, filename), *args, **kwargs)
