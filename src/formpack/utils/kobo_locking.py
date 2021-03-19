# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import io
import itertools

from .xls_to_ss_structure import xls_to_dicts

KOBO_LOCK_SHEET = 'kobo--locking-profiles'
POSITIVE_SELECTIONS = (
    'yes',
    "Yes",
    'YES',
    'true',
    'True',
    'TRUE',
)
KOBO_LOCKING_RESTRICTIONS = (
    'choice_add',
    'choice_delete',
    'choice_edit',
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
    'form_replace',
    'group_add',
    'question_add',
    'question_order_edit',
    'translations_manage',
    'form_appearance',
)

def get_kobo_locking_profiles(xls_file_object: io.BytesIO) -> list:
    """
    Return the locking profiles if there are any
    """
    survey_dict = xls_to_dicts(xls_file_object)
    if KOBO_LOCK_SHEET not in survey_dict:
        return

    locks = survey_dict.get(KOBO_LOCK_SHEET)
    profiles = set(itertools.chain(*[list(lock.keys()) for lock in locks]))
    profiles.remove('restriction')
    locking_profiles = {
        name: dict(name=name, restrictions=[]) for name in profiles
    }

    for lock in locks:
        for name in profiles:
            if lock.get(name) in POSITIVE_SELECTIONS:
                locking_profiles[name]['restrictions'].append(
                    lock.get('restriction')
                )

    return list(locking_profiles.values())

def revert_kobo_lock_structre(content: dict) -> None:
    if KOBO_LOCK_SHEET not in content:
        return
    locking_profiles = []
    for res in KOBO_LOCKING_RESTRICTIONS:
        profile = {'restriction': res}
        for item in content[KOBO_LOCK_SHEET]:
            name = item['name']
            restrictions = item['restrictions']
            if res in restrictions:
                profile[name] = 'true'
        locking_profiles.append(profile)
    content[KOBO_LOCK_SHEET] = locking_profiles

