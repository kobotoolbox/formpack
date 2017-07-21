import json
from copy import deepcopy
from collections import OrderedDict, defaultdict

from pyxform import aliases as pyxform_aliases
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT


TF_COLUMNS = [
    'required',
]


def aliases_to_ordered_dict(_d):
    '''
    unpacks a dict-with-lists to an ordered dict with keys sorted by length
    '''
    arr = []
    for (original, aliases) in _d.items():
        arr.append((original, original))
        if isinstance(aliases, bool):
            aliases = [original]
        elif isinstance(aliases, basestring):
            aliases = [aliases]
        for alias in aliases:
            arr.append((alias, original,))
    return OrderedDict(sorted(arr, key=lambda _kv: 0-len(_kv[0])))


TYPES = aliases_to_ordered_dict({
    u'begin_group': [
        u'begin group',
        u'begin  group',
    ],
    u'end_group': [
        u'end group',
        u'end  group'
    ],
    u'begin_repeat': [
        u'begin lgroup',
        u'begin repeat',
        u'begin looped group',
    ],
    u'end_repeat': [
        u'end lgroup',
        u'end repeat',
        u'end looped group',
    ],
    'text': ['string'],
    'acknowledge': ['trigger'],
    'image': ['photo'],
    'datetime': ['dateTime'],
    'deviceid': ['imei'],
    'geopoint': ['gps'],
})

SELECTS = aliases_to_ordered_dict({
    u'select_multiple': [
        u'select all that apply',
        u'select multiple',
        u'select many',
        u'select_many',
        u'select all that apply from',
        u'add select multiple prompt using',
    ],
    u'select_one_external': [
        u'select one external',
    ],
    u'select_one': [
        u'select one',
        u'select one from',
        u'add select one prompt using',
        u'select1',
    ],
})

SELECT_TYPES = SELECTS.keys()

META_TYPES = [
    'start',
    'today',
    'end',
    'deviceid',
    'phone_number',
    'simserial',
    # meta values
    'username',
    # reconsider:
    'phonenumber',
    'imei',
    'subscriberid',
]

LABEL_OPTIONAL_TYPES = [
    'calculate',
    'begin_group',
    'begin_repeat',
] + META_TYPES

GEO_TYPES = [
    'gps',
    'geopoint',
    'geoshape',
    'geotrace',
]

MAIN_TYPES = [
    # basic entry
    'text',
    'integer',
    'decimal',
    'email',
    'barcode',
    # collect media
    'video',
    'image',
    'audio',
    # enter time values
    'date',
    'datetime',
    'time',

    # prompt to collect geo data
    'location',

    # no response
    'acknowledge',
    'note',
] + GEO_TYPES
formpack_preferred_types = set(MAIN_TYPES + LABEL_OPTIONAL_TYPES + SELECTS.keys())

_pyxform_type_aliases = defaultdict(list)
_formpack_type_reprs = {}

for (_type, val) in QUESTION_TYPE_DICT.items():
    _xform_repr = json.dumps(val, sort_keys=True)
    if _type in formpack_preferred_types:
        _formpack_type_reprs[_type] = _xform_repr
    else:
        _pyxform_type_aliases[_xform_repr].append(_type)

formpack_type_aliases = aliases_to_ordered_dict(dict([
        (_type, _pyxform_type_aliases[_repr])
        for (_type, _repr) in _formpack_type_reprs.items()
    ]))


KNOWN_TYPES = set(QUESTION_TYPE_DICT.keys() + SELECTS.values() + TYPES.values())


def _unpack_headers(p_aliases, fp_preferred):
    _aliases = p_aliases.copy().items()
    combined = dict([
        (key, val if (val not in fp_preferred) else fp_preferred[val])
        for (key, val) in _aliases
    ] + fp_preferred.items())
    # ensure that id_string points to id_string (for example)
    combined.update(dict([
        (val, val) for val in combined.values()
    ]))
    return combined

formpack_preferred_settings_headers = {
    'title': 'form_title',
    'form_id': 'id_string',
}
SETTINGS_RENAMES = _unpack_headers(pyxform_aliases.settings_header,
                                   formpack_preferred_settings_headers)

# this opts out of columns with '::' (except media columns)
formpack_preferred_survey_headers = {
    'bind::calculate': 'calculation',
    'bind::required': 'required',
    'bind::jr:requiredMsg': 'required_message',
    'bind::relevant': 'relevant',
    'bind::jr:constraintMsg': 'constraint_message',
    'bind::constraint': 'constraint',
    'bind::readonly': 'read_only',
    'control::jr:count': 'repeat_count',
    'control::appearance': 'appearance',
    'control::rows': 'rows',
    'control::autoplay': 'autoplay',
    'bind::jr:noAppErrorString': 'no_app_error_string',
}

SURVEY_RENAMES = _unpack_headers(pyxform_aliases.survey_header,
                                 formpack_preferred_survey_headers)
