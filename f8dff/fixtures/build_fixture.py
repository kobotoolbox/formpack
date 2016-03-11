# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import importlib


def build_fixture(modulename):
    return importlib.import_module('..%s' % modulename, __name__).DATA
