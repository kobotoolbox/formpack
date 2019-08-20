# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
import io
import os
import importlib
from copy import deepcopy


def build_fixture(modulename, data_variable_name="DATA"):
    fixtures = deepcopy(getattr(importlib.import_module('..%s' % modulename, __name__), data_variable_name))

    if 'submissions_xml' in fixtures:
        # This fixture contains XML submissions, which apparently aren't used
        # for anything yet; see
        # `TestFormPackFixtures.test_xml_instances_loaded()`.
        # Example XML fixture: tests/fixtures/favcolor/xml_instances.json
        return fixtures

    title = fixtures.get('title')

    # separate the submissions from the schema
    schemas = [dict(v) for v in fixtures['versions']]
    submissions = []
    for schema in schemas:
        version = schema.get('version')
        version_id_key = schema.get('version_id_key', '__version__')
        for submission in schema.pop('submissions'):
            submission.update({version_id_key: version})
            submissions.append(submission)
    return title, schemas, submissions


def open_fixture_file(modulename, filename, *args, **kwargs):
    """
    Open a file included with a text fixture, e.g. the expected output of an
    export. Not used to load test fixture schema/submission JSON data
    """
    fixture_dir = os.path.dirname(
        os.path.abspath(
            importlib.import_module('..%s' % modulename, __name__).__file__
        )
    )
    return io.open(os.path.join(fixture_dir, filename), encoding='utf-8', *args, **kwargs)
