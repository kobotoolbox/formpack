# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

# In the core formpack code, the default `lang` parameter conflicted
# with the desired representation of the JSON form, where "null" would
# represent the untranslated value.

# These two constants can be set to different values but they must
# not be equal.
# User-specified translations would always be a string,
# thus should never the boolean `False`.
# When formpack cannot find a label for the requested translation, it returns the XML name instead.
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

# The Excel format supports worksheet names as long as 255 characters, but in
# practice the Excel application has a 31-character limit.
# http://stackoverflow.com/a/3681908
EXCEL_SHEET_NAME_SIZE_LIMIT = 31

# Some characters are forbidden from worksheet names
EXCEL_FORBIDDEN_WORKSHEET_NAME_CHARACTERS = r'[]*?:\/'

# Tag columns are tags that have their own columns when expanding and
# flattening. Internally, they are stored as tags prefixed with their column
# name and a colon, e.g.
#
#   name           | hxl       | tags
#   ---------------+-----------+-----------------
#   family_members | #affected | urban population
#
# is stored internally as tags ['hxl:affected', 'urban', 'population']
TAG_COLUMNS_AND_SEPARATORS = {
    # Separators are used when flattening tags into a single column. Keys are
    # column names, values are separators.
    'hxl': '',
}
