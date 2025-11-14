import pytest

from formpack import FormPack
from formpack.errors import TranslationError
from formpack.utils.expand_content import expand_content


def test_big_image_with_other_media_types_works_correctly():
    content = {
        'survey': [
            {
                'type': 'select_one',
                'name': 'q_multi_media',
                'label': 'Question with multiple media',
                'media::image': 'small.png',
                'big-image': 'large.png',
                'select_from_list_name': 'opts',
            }
        ],
        'choices': [
            {'list_name': 'opts', 'name': 'a', 'label': 'Option A'},
        ],
        'translations': [None],
    }

    expand_content(content, in_place=True)

    # All media should be in translated
    translated = content.get('translated', [])
    assert 'media::image' in translated
    assert 'media::big-image' in translated

    # Only NONE should be in translations
    assert 'big-image' not in content['translations']
    assert 'image' not in content['translations']

    # FormPack should process without errors
    fp = FormPack([{'content': content, 'version': 1}], 'Test')
    assert len(fp.versions) == 1


def test_formpack_raises_error_when_big_image_not_in_media_names(monkeypatch):
    """
    Test that FormPack raises an error when `big-image` is used
    but not included in media names
    """
    content = {
        'survey': [
            {
                'type': 'select_one',
                'name': 'q_with_big_image',
                'label': 'Question with big image',
                'big-image': 'large.png',
                'select_from_list_name': 'opts',
            }
        ],
        'choices': [
            {'list_name': 'opts', 'name': 'a', 'label': 'Option A'},
        ],
        'translations': [None],
    }

    # Patch MEDIA_COLUMN_NAMES to exclude 'big-image'
    monkeypatch.setattr(
        'formpack.utils.expand_content.MEDIA_COLUMN_NAMES',
        ('image', 'audio', 'video')
    )
    expand_content(content, in_place=True)

    with pytest.raises(TranslationError):
        FormPack([{'content': content, 'version': 1}], 'Test')
