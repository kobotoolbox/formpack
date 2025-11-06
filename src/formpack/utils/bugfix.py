# coding: utf-8

from copy import deepcopy

from ..constants import UNTRANSLATED


def repair_media_column_content_in_place(content) -> bool:
    """
    #321 introduced a bug where the `file` column gets renamed to `media::file`
    and treated as a translatable column (see #322). This function repairs that
    damage.

    It also handles other `media::<type>` columns similarly affected by the same bug.

    This function is intended to be run by KPI, which should use it to correct
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

    media_tokens = [
        t for t in updates['translated'] if isinstance(t, str) and t.startswith('media::')
    ]
    if not media_tokens:
        # No media::<type> in translated, nothing to do
        return False

    # Remove the media tokens from translated
    for token in media_tokens:
        try:
            updates['translated'].remove(token)
        except ValueError:
            pass

    max_label_list_length = 0
    any_row_fixed = False
    for row in updates['survey']:
        max_label_list_length = max(
            max_label_list_length, len(row.get('label', []))
        )

        # For each media token, handle its value:
        # - If value is a list, pick first non-None and migrate it.
        # - If scalar, migrate it.
        for media_tok in media_tokens:
            bad_val = row.get(media_tok)
            if bad_val is None:
                continue

            # If it's a list (the broken shape), prefer the first non-None element
            if isinstance(bad_val, list):
                non_nulls = [v for v in bad_val if v is not None]
                if not non_nulls:
                    try:
                        del row[media_tok]
                    except KeyError:
                        pass
                    any_row_fixed = True
                    continue

                chosen = non_nulls[0]
                short_key = media_tok.split('::', 1)[1]
                row[short_key] = chosen
                try:
                    del row[media_tok]
                except KeyError:
                    pass
                any_row_fixed = True
                continue

            # Scalar value: migrate it directly
            short_key = media_tok.split('::', 1)[1]
            row[short_key] = bad_val
            try:
                del row[media_tok]
            except KeyError:
                pass
            any_row_fixed = True

    if not any_row_fixed:
        return False

    # Multi-language forms need an additional fix to remove a superfluous null
    # translation added by the bogus `media::*` column(s)
    if len(updates['translations']) > max_label_list_length:
        labels_translations_mismatch = True
        if len(updates['translations']) == max_label_list_length + 1:
            try:
                if UNTRANSLATED is not None:
                    updates['translations'].remove(UNTRANSLATED)
                    labels_translations_mismatch = False
                else:
                    # If sentinel not present, remove a media tail name
                    tails = [m.split('::', 1)[1] for m in media_tokens]
                    removed = False
                    for t in tails:
                        try:
                            updates['translations'].remove(t)
                            removed = True
                            break
                        except ValueError:
                            continue
                    if removed:
                        labels_translations_mismatch = False
                    else:
                        updates['translations'].pop()
                        labels_translations_mismatch = False
            except ValueError:
                pass

        if labels_translations_mismatch:
            # This form has uncorrected problems. Bail out instead of modifying
            # it at all
            return False

    # Success! Apply updates to the original content
    content.update(updates)
    return True
