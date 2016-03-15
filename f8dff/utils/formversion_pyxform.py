# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from pyxform.xls2json import workbook_to_json
from pyxform.builder import create_survey_element_from_dict


def formversion_pyxform(data):
    content = data.get('content')
    imported_survey_json = workbook_to_json(content)
    return create_survey_element_from_dict(imported_survey_json)
