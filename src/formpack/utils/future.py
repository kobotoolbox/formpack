# coding: utf-8
from collections import OrderedDict
from io import StringIO

#    range = range
#    unichr = chr

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
