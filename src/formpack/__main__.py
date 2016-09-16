# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


import begin

import sys
import json
from formpack import FormPack
from .utils.xls_to_ss_structure import xls_to_dicts
from .utils.expand_content import expand_content
from .utils.flatten_content import flatten_content


def print_xls(filename, expand=False, flatten=False, xml=False):
    '''
    converts and XLS file with many sheets to a JSON object with lists
    of key-value pairs for each row in the sheet.
    '''
    try:
        with open(filename, 'r') as ff:
            content = xls_to_dicts(ff)
            if expand:
                expand_content(content)
                settings = content.get('settings', {})
                settings['title'] = settings.get('title', 'title')
                settings['id_string'] = settings.get('id_string', 'id_string')
                content['settings'] = [settings]
            if flatten:
                flatten_content(content)
            settings = content.pop('settings', [{}])[0]
            if xml:
                print(FormPack({'content': content}, **settings)[0].to_xml())
            else:
                print(json.dumps(content,
                                 indent=2))
    except EnvironmentError, e:
        sys.exit('error trying to read input as xls file? {}: {}'.format(
                 filename, e))


@begin.subcommand
def xls(filename, expand=False, flatten=False, xml=False):
    kwargs = {
        'expand': expand,
        'flatten': flatten,
        'xml': xml,
    }
    print_xls(filename, **kwargs)

@begin.subcommand
def xlse(filename):
    print_xls(filename, expand=True)

@begin.subcommand
def xlsef(filename):
    print_xls(filename, expand=True, flatten=True)

@begin.start
def run():
    pass
