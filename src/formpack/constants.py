# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

# In the core formpack code, the default `lang` parameter conflicted
# with the desired representation of the JSON form, where "null" would
# represent the untranslated value.

# These two constants can be set to different values but they must
# not be equal
UNSPECIFIED_TRANSLATION = False

# This `UNTRANSLATED` will correspond to `null` in the schema where
#   [{"label": ["X", "En", "Fr"]}]
#   ...
#   "translations": [null, "English", "French"]
#
# compiles to the xlsform values of
#   label | label::En | label::Fr
#   ------+-----------+----------
#   X     | En        | Fr
UNTRANSLATED = None
