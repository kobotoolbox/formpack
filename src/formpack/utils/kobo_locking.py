# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import io
import itertools

from .xls_to_ss_structure import xls_to_dicts

POSITIVE_SELECTIONS = (
    "yes",
    "Yes",
    "YES",
    "true",
    "True",
    "TRUE",
)

def get_kobo_locking_profiles(xls_file_object: io.BytesIO) -> list:
    """
    Return the locking profiles if there are any
    """
    KOBO_LOCKS = 'kobo--locks'
    survey_dict = xls_to_dicts(xls_file_object)
    if KOBO_LOCKS not in survey_dict:
        return

    locks = survey_dict.get(KOBO_LOCKS)
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

