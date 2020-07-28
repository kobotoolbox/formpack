# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
import io
import json
import os
import importlib
from copy import deepcopy


from a1d05eba1 import Content

import os

_FILE = os.path.abspath(__file__)
_DIR = os.path.dirname(_FILE)
JSON_FIXTURES_DIR = os.path.join(_DIR, 'json')

def build_fixture(modulename, data_variable_name="DATA"):
    fixture_path = os.path.join(JSON_FIXTURES_DIR, '{}.json'.format(modulename))
    schemas = []
    with open(fixture_path, 'r') as ff:
        infile = json.loads(ff.read())
        _versions = infile['versions']
        _titles = []
        _ids = []
        for vv in _versions:
            _titles.append(vv['settings']['title'])
            _ids.append(vv['settings']['identifier'])
            schemas.append(vv)
        assert len(set(_titles)) == 1
        assert len(set(_ids)) == 1
        _submissions = infile['submissions']
    return _titles[0], schemas, _submissions


def open_sps_fixture_file(filename):
    """
    Open a file included with a text fixture, e.g. the expected output of an
    export. Not used to load test fixture schema/submission JSON data
    """
    sps_filename = os.path.join(_DIR, 'sps', filename)
    return io.open(sps_filename, 'r', encoding='utf-8')

def open_b64_images_file(filename):
    images_filename = os.path.join(_DIR, 'b64_images', filename + '.json')
    with open(images_filename, 'r') as ff:
        content_ = ff.read()
        return json.loads(content_)
