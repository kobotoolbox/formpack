import importlib


def build_fixture(modulename):
    return importlib.import_module('f8dff.fixtures.%s' % modulename).DATA
