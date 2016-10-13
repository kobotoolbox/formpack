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

# the column used to denote "or_other" in a select question type
# this is non-standard XLSForm
OR_OTHER_COLUMN = '_or_other'
# in the long run, the "select_one x or_other" syntax should be deprecated
# because the or_other strings are not translatable
