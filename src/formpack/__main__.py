# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


import begin

import sys
import json
from .utils.xls_to_ss_structure import xls_to_dicts


@begin.subcommand
def xls(filename):
    '''
    converts and XLS file with many sheets to a JSON object with lists
    of key-value pairs for each row in the sheet.
    '''
    try:
        with open(filename, 'r') as ff:
            print(json.dumps(xls_to_dicts(ff),
                             indent=2))
    except EnvironmentError, e:
        sys.exit('error trying to read input as xls file? {}: {}'.format(
                 filename, e))


@begin.start
def run():
    pass
