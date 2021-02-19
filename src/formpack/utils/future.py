# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    range = xrange
except NameError:
    range = range


try:
    unichr = unichr
except NameError:
    unichr = chr

import sys

# These helpers are duplicated from `six`.
# When FormPack stops support for Python2, this file can be removed and code
# can be replaced with Python3 code
PY2 = sys.version_info[0] == 2


def iteritems(d, **kw):
    if PY2:
        return d.iteritems(**kw)
    else:
        return iter(d.items(**kw))


def itervalues(d, **kw):
    if PY2:
        return d.itervalues(**kw)
    else:
        return iter(d.values(**kw))
