# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
This file provides a way to open production data and
write a test based on that data.
'''
import os
import glob
import json
from collections import defaultdict


DIR = os.path.dirname(os.path.abspath(__file__))


def _path(*args):
    return os.path.join(DIR, *args)

def _load_version_file(vf):
    with open(vf, 'r') as version_f:
        vx = json.loads(version_f.read())
        uid = vx.pop('uid')
        vx.update({
            'version': uid,
            'submissions': submissions.get(uid, [])
        })
        return vx

with open(_path('asset.json'), 'r') as asset_file:
    asset = json.loads(asset_file.read())

with open(_path('data.json'), 'r') as submission_f:
    submissions = defaultdict(list)
    for submission in json.loads(submission_f.read()):
        vkey = submission['__version__']
        submissions[vkey].append(submission)

_version_file_list = glob.glob(_path('versions', '*'))


DATA = {
    'title': asset['name'],
    'versions': [_load_version_file(vf) for vf in _version_file_list],
    'submissions': submissions,
}
