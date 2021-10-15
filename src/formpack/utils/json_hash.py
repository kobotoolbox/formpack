# -*- coding: utf-8 -*-
import hashlib
import json


def json_hash(obj, size=8):
    size = size % 39
    if size < 1:
        raise ValueError('json_hash size parameter must be in range(1, 39)')
    _json_string = json.dumps(obj, sort_keys=True)

    return hashlib.sha1(_json_string.encode('utf-8')).hexdigest()[0:size]
