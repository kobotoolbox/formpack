import os
import json
CUR_DIR = os.path.dirname(os.path.abspath(__file__))


def load_fixture_json(fname):
    with open(os.path.join(CUR_DIR, '%s.json' % fname)) as ff:
        return json.loads(ff.read().decode('utf8'))
