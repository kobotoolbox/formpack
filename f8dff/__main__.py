import begin

import os
import json
from utils.xls_to_ss_structure import xls_to_dicts

@begin.subcommand
def xls(filename):
    try:
        with open(filename, 'r') as ff:
            print(json.dumps(xls_to_dicts(ff),
                             indent=2))
    except IOError, e:
        print('file exists? {}'.format(filename))

@begin.start
def run():
    pass
