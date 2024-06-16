# coding: utf-8

from copy import deepcopy

from ..constants import UNTRANSLATED


def repair_file_column_content_in_place(content) -> bool:
    """
    #321 introduced a bug where the `file` column gets renamed to `media::file`
    and treated as a translatable column (see #322). This function repairs that
    damage.

    This function is intended to be run by KPI, which should it to correct
    `Asset` and `AssetVersion` content.

    Returns `True` if any change was made
    """

    # Store updates and apply them to `content` only of all conditions are met
    updates = {}

    try:
        for key in 'translated', 'translations', 'survey':
            updates[key] = deepcopy(content[key])
    except KeyError:
        # Do not proceed if content is incomplete
        return False

    try:
        updates['translated'].remove('media::file')
    except ValueError:
        # The invalid column `media::file` inside `translated` is a hallmark of
        # the problem this method is intended to fix. Do not proceed if it was
        # not found
        return False

    max_label_list_length = 0
    any_row_fixed = False
    for row in updates['survey']:
        max_label_list_length = max(
            max_label_list_length, len(row.get('label', []))
        )
        bad_file_col = row.get('media::file')
        if not bad_file_col:
            continue
        if not isinstance(bad_file_col, list):
            # All problems of our own making (#322) will result in
            # `media::file` being a list (or array when JSON)
            continue
        for val in bad_file_col:
            if val is not None:
                row['file'] = val
                del row['media::file']
                any_row_fixed = True
                break
    if not any_row_fixed:
        return False

    # Multi-language forms need an additional fix to remove a superfluous null
    # translation added by the bogus `media::file` column
    if len(updates['translations']) > max_label_list_length:
        labels_translations_mismatch = True
        if len(updates['translations']) == max_label_list_length + 1:
            try:
                updates['translations'].remove(UNTRANSLATED)
            except ValueError:
                pass
            else:
                labels_translations_mismatch = False  # Fixed it!
        if labels_translations_mismatch:
            # This form has uncorrected problems. Bail out instead of modifying
            # it at all
            return False

    # Success! Apply updates to the original content
    content.update(updates)
    return True
