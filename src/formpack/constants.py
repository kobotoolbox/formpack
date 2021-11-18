# coding: utf-8

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

# This constant is used to signify that the arg header_lang is not set
UNSPECIFIED_HEADER_LANG = "UNSPECIFIED_HEADER_LANG"

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

GEO_QUESTION_TYPES = ('geopoint', 'geotrace', 'geoshape')

# Export Settings
EXPORT_SETTING_FIELDS = 'fields'
EXPORT_SETTING_FIELDS_FROM_ALL_VERSIONS = 'fields_from_all_versions'
EXPORT_SETTING_FLATTEN = 'flatten'
EXPORT_SETTING_GROUP_SEP = 'group_sep'
EXPORT_SETTING_HIERARCHY_IN_LABELS = 'hierarchy_in_labels'
EXPORT_SETTING_INCLUDE_MEDIA_URL = 'include_media_url'
EXPORT_SETTING_LANG = 'lang'
EXPORT_SETTING_MULTIPLE_SELECT = 'multiple_select'
EXPORT_SETTING_NAME = 'name'
EXPORT_SETTING_QUERY = 'query'
EXPORT_SETTING_SOURCE = 'source'
EXPORT_SETTING_SUBMISSION_IDS = 'submission_ids'
EXPORT_SETTING_TYPE = 'type'
EXPORT_SETTING_XLS_TYPES_AS_TEXT = 'xls_types_as_text'
OPTIONAL_EXPORT_SETTINGS = [
    EXPORT_SETTING_FIELDS,
    EXPORT_SETTING_FLATTEN,
    EXPORT_SETTING_INCLUDE_MEDIA_URL,
    EXPORT_SETTING_NAME,
    EXPORT_SETTING_QUERY,
    EXPORT_SETTING_SUBMISSION_IDS,
    EXPORT_SETTING_XLS_TYPES_AS_TEXT,
]
REQUIRED_EXPORT_SETTINGS = [
    EXPORT_SETTING_FIELDS_FROM_ALL_VERSIONS,
    EXPORT_SETTING_GROUP_SEP,
    EXPORT_SETTING_HIERARCHY_IN_LABELS,
    EXPORT_SETTING_LANG,
    EXPORT_SETTING_MULTIPLE_SELECT,
    EXPORT_SETTING_TYPE,
]
VALID_EXPORT_SETTINGS = OPTIONAL_EXPORT_SETTINGS + REQUIRED_EXPORT_SETTINGS

MULTIPLE_SELECT_BOTH = 'both'
MULTIPLE_SELECT_DETAILS = 'details'
MULTIPLE_SELECT_SUMMARY = 'summary'
VALID_MULTIPLE_SELECTS = [
    MULTIPLE_SELECT_BOTH,
    MULTIPLE_SELECT_DETAILS,
    MULTIPLE_SELECT_SUMMARY,
]

EXPORT_TYPE_CSV = 'csv'
EXPORT_TYPE_GEOJSON = 'geojson'
EXPORT_TYPE_SPSS = 'spss_labels'
EXPORT_TYPE_XLS = 'xls'
VALID_EXPORT_TYPES = [
    EXPORT_TYPE_CSV,
    EXPORT_TYPE_GEOJSON,
    EXPORT_TYPE_SPSS,
    EXPORT_TYPE_XLS,
]

DEFAULT_LANG = '_default'
DEFAULT_LANG_XML = '_xml'
VALID_DEFAULT_LANGUAGES = [
    DEFAULT_LANG,
    DEFAULT_LANG_XML,
]

FALSE = 'false'
TRUE = 'true'
VALID_BOOLEANS = [
    FALSE,
    TRUE,
]

# Kobo locking constants
KOBO_LOCK_ALL = 'kobo--lock_all'
KOBO_LOCK_COLUMN = 'kobo--locking-profile'
KOBO_LOCK_KEY = 'locked'
KOBO_LOCK_SHEET = 'kobo--locking-profiles'
KOBO_LOCKING_RESTRICTIONS = [
    'choice_add',
    'choice_delete',
    'choice_label_edit',
    'choice_value_edit',
    'choice_order_edit',
    'question_delete',
    'question_label_edit',
    'question_settings_edit',
    'question_skip_logic_edit',
    'question_validation_edit',
    'group_delete',
    'group_label_edit',
    'group_question_add',
    'group_question_delete',
    'group_question_order_edit',
    'group_settings_edit',
    'group_skip_logic_edit',
    'group_split',
    'form_replace',
    'group_add',
    'question_add',
    'question_order_edit',
    'language_edit',
    'form_appearance',
    'form_meta_edit',
]
