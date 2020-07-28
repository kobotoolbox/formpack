from pyxform.xls2json import workbook_to_json

from pyxform.builder import create_survey_element_from_dict

from a1d05eba1 import Content
from a1d05eba1.utils.kfrozendict import kfrozendict
from a1d05eba1.utils.kfrozendict import deepfreeze


def content_to_xform(content):
    content = deepfreeze(content)

    settings = content['settings']
    cc = Content(content.copy(settings=settings))

    # tx_names is passed to the pyxform object to ensure the itext
    # translations show up in the correct order
    tx_names = []
    for tx in cc.txs.to_v1_strings():
        if tx is not None:
            tx_names.append(tx)

    flat_json = cc.export(schema='xlsform')
    flat_json.pop('schema')
    wbjson = workbook_to_json(flat_json)
    survey = create_survey_element_from_dict(wbjson)
    # title = self._get_title()
    title = content['settings'].get('title')

    if title is None:
        raise ValueError('cannot create xml on a survey with no title.')

    for tx_name in tx_names:
        survey._translations[tx_name] = {}

    return survey._to_pretty_xml()
