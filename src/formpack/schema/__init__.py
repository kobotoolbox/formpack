# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)


from functools import partial

from .fields import *  # noqa
from .datadef import *  # noqa


def _field_from_dict(definition, hierarchy=None,
                     section=None, field_choices={},
                     translations=None):
    """Return an instance of a Field class matching this JSON field def

    Depending of the data datype extracted from the field definition,
    this method will return an instance of a different class.

    Args:
        definition (dict): Description
        group (FormGroup, optional): The group this field is into
        section (FormSection, optional): The section this field is into
        field_choices (dict, optional):
            A mapping of all the FormChoice instances available for
            this form.

    Returns:
        Union[FormChoiceField, FormChoiceField,
              FormChoiceFieldWithMultipleSelect, FormField]:
              The FormField instance matching this definiton.
    """
    name = definition.get('$autoname', definition.get('name'))
    label = definition.get('label')
    if label:
        labels = OrderedDict(zip(translations, label))
    else:
        labels = {}

    # normalize spaces
    data_type = definition['type']
    choice = None

    if ' ' in data_type:
        raise ValueError('invalid data_type: %s' % data_type)

    if data_type in ('select_one', 'select_multiple'):
        choice_id = definition['select_from_list_name']
        choice = field_choices[choice_id]

    data_type_classes = {
        "select_one": FormChoiceField,
        "select_multiple": FormChoiceFieldWithMultipleSelect,
        "geopoint": FormGPSField,
        "date": DateField,
        "text": TextField,
        "barcode": TextField,

        # calculate is usually not text but for our purpose it's good
        # enough
        "calculate": TextField,
        "acknowledge": TextField,
        "integer": NumField,
        'decimal': NumField,

        # legacy type, treat them as text
        "select_one_external": partial(TextField, data_type=data_type),
        "cascading_select": partial(TextField, data_type=data_type),
    }

    cls = data_type_classes.get(data_type, FormField)
    return cls(name=name,
               labels=labels,
               data_type=data_type,
               hierarchy=hierarchy,
               section=section,
               choice=choice,
               src=definition,
               )
