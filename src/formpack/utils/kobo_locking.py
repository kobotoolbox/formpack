# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import io
import itertools
from collections import OrderedDict

from pyxform import aliases as pyxform_aliases

from .xls_to_ss_structure import xls_to_dicts
from formpack.constants import (
    KOBO_LOCKING_RESTRICTIONS,
    KOBO_LOCK_COLUMN,
    KOBO_LOCK_SHEET,
)

def get_kobo_locking_profiles(xls_file_object: io.BytesIO) -> list:
    """
    Return the locking profiles if there are any in a dictionary structure from
    an XLSForm matrix. For example, the following matrix structure:

    # kobo--locking-profiles
    |    restriction    | profile_1 | profile_2 |
    |-------------------|-----------|-----------|
    | choice_add        | True      |           |
    | choice_delete     |           | True      |
    | choice_edit       | True      |           |
    | choice_order_edit | True      | True      |

    Will be transformed into the following JSON structure:
    [
        {
            "name": "profile_1",
            "restrictions": [
                "choice_add",
                "choice_edit",
                "choice_order_edit"
            ],
        },
        {
            "name": "profile_2",
            "restrictions": [
                "choice_delete",
                "choice_order_edit"
            ],
        }
    ]
    """
    survey_dict = xls_to_dicts(xls_file_object)
    if KOBO_LOCK_SHEET not in survey_dict:
        return

    locks = survey_dict.get(KOBO_LOCK_SHEET)
    # Get a unique list of profile names if they have at least one value set to
    # `True` (or whatever valid "positive selection" value) from the matrix of
    # values
    profiles = set(itertools.chain(*[lock.keys() for lock in locks]))

    if 'restriction' not in profiles:
        raise KeyError('The column name `restriction` must be present')

    # Remove the `restriction` column header from the list to only have the
    # predefined profile names
    profiles.remove('restriction')

    # Set up an indexed dictionary for convenience -- return only its values
    locking_profiles = {
        name: dict(name=name, restrictions=[]) for name in profiles
    }

    for lock in locks:
        restriction = lock.get('restriction')
        # ensure that valid lock values are being used
        if restriction not in KOBO_LOCKING_RESTRICTIONS:
            raise KeyError
        for name in profiles:
            bool_value = lock.get(name, False)
            if pyxform_aliases.yes_no.get(bool_value, False):
                locking_profiles[name]['restrictions'].append(restriction)

    return list(locking_profiles.values())

def revert_kobo_lock_structre(content: dict) -> None:
    """
    Revert the structure of the locks to one that is ready to be exported into
    an XLSForm again -- the reverse of `get_kobo_locking_profiles`

    It is essentially a preprocessor used within KPI before converting all the
    sheets and content to OrderedDicts and exporting to XLS.

    For example, this JSON structure:
    [
        {
            "name": "profile_1",
            "restrictions": [
                "choice_add",
                "choice_edit",
                "choice_order_edit"
            ],
        },
        {
            "name": "profile_2",
            "restrictions": [
                "choice_delete",
                "choice_order_edit"
            ],
        }
    ]

    Will be transformed into:
    [
        {
            'restriction': 'choice_add',
            'profile_1': True,
        },
        {
            'restriction': 'choice_edit',
            'profile_1': True,
        },
        {
            'restriction': 'choice_order_edit',
            'profile_1': True,
            'profile_2': True,
        },
        {
            'restriction': 'choice_delete',
            'profile_2': True,
        },
    ]
    """
    if KOBO_LOCK_SHEET not in content:
        return
    locking_profiles = []
    for res in KOBO_LOCKING_RESTRICTIONS:
        profile = {'restriction': res}
        for item in content[KOBO_LOCK_SHEET]:
            name = item['name']
            restrictions = item['restrictions']
            if res in restrictions:
                profile[name] = True
        locking_profiles.append(profile)
    content[KOBO_LOCK_SHEET] = locking_profiles

def strip_kobo_locking_profile(content: OrderedDict) -> None:
    """
    Strip all `kobo--locking-profile` values from a survey. Used when creating
    blocks or adding questions to the library from a locked survey or template.
    The locks should only be applied on survey and template types.
    """
    survey = content.get('survey')
    for item in survey:
      if KOBO_LOCK_COLUMN in item:
          item.pop(KOBO_LOCK_COLUMN)

