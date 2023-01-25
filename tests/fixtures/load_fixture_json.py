# coding: utf-8
import os
import json

CUR_DIR = os.path.dirname(os.path.abspath(__file__))


def load_fixture_json(fname):
    with open(os.path.join(CUR_DIR, '%s.json' % fname)) as ff:
        content_ = ff.read()
        return json.loads(content_)


def load_analysis_form_json(path):
    with open(os.path.join(CUR_DIR, path, 'analysis_form.json')) as f:
        return json.loads(f.read())
