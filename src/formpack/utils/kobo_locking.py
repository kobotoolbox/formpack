# coding: utf-8
import io
import itertools
from collections import OrderedDict

from .xls_to_ss_structure import xls_to_dicts
from formpack.constants import (
    KOBO_LOCKING_RESTRICTIONS,
    KOBO_LOCK_COLUMN,
    KOBO_LOCK_KEY,
    KOBO_LOCK_SHEET,
)
from formpack.utils.exceptions import FormPackLibraryLockingError


def get_kobo_locking_profiles(xls_file_object: io.BytesIO) -> list:
    """
    Return the locking profiles, if there are any, in a dictionary structure
    from an XLSForm matrix. For example, the following matrix structure:

    # kobo--locking-profiles
    |    restriction    | profile_1 | profile_2 |
    |-------------------|-----------|-----------|
    | choice_add        | locked    |           |
    | choice_delete     |           | locked    |
    | choice_label_edit | locked    |           |
    | choice_order_edit | locked    | locked    |

    Will be transformed into the following JSON structure:
    [
        {
            "name": "profile_1",
            "restrictions": [
                "choice_add",
                "choice_label_edit",
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

    locks = survey_dict[KOBO_LOCK_SHEET]

    # Get a unique list of profile names
    profiles = set()
    for lock in locks:
        profiles.update(lock.keys())

    # So some basic validation of locking profiles
    profiles = _validate_locking_profiles(profiles)

    # Set up an indexed dictionary for convenience -- return only its values
    locking_profiles = {
        name: dict(name=name, restrictions=[]) for name in profiles
    }

    for lock in locks:
        restriction = lock.get('restriction')
        # ensure that valid lock values are being used
        if restriction not in KOBO_LOCKING_RESTRICTIONS:
            raise FormPackLibraryLockingError(
                f'{restriction} is not a valid restriction.'
            )
        for name in profiles:
            if lock.get(name, '').lower() == KOBO_LOCK_KEY:
                locking_profiles[name]['restrictions'].append(restriction)

    return list(locking_profiles.values())


def revert_kobo_lock_structure(content: dict) -> None:
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
                "choice_label_edit",
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
            'profile_1': 'locked',
        },
        {
            'restriction': 'choice_label_edit',
            'profile_1': 'locked',
        },
        {
            'restriction': 'choice_order_edit',
            'profile_1': 'locked',
            'profile_2': 'locked',
        },
        {
            'restriction': 'choice_delete',
            'profile_2': 'locked',
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
                profile[name] = KOBO_LOCK_KEY
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


def _validate_locking_profiles(profiles):
    """
    Some simple validation of the locking profiles to provide helpful error
    messages to the user
    """
    if 'restriction' not in profiles:
        raise FormPackLibraryLockingError(
            'The column name `restriction` must be present.'
        )

    # Remove the `restriction` column header from the list to only have the
    # user-defined profile names
    profiles.remove('restriction')

    if not profiles:
        raise FormPackLibraryLockingError(
            'At least one locking profile must be defined.'
        )

    if KOBO_LOCK_KEY in profiles:
        raise FormPackLibraryLockingError(
            f'Locking profile name of "{KOBO_LOCK_KEY}" cannot be used.'
        )

    return profiles
