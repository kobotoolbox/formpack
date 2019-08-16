# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import os
import json
CUR_DIR = os.path.dirname(os.path.abspath(__file__))


def load_fixture_json(fname):
    with open(os.path.join(CUR_DIR, '%s.json' % fname)) as ff:
        content_ = ff.read()
        return json.loads(content_)
