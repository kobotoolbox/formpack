# coding: utf-8
import json
from copy import deepcopy

import pytest

from formpack import FormPack
from formpack.constants import UNSPECIFIED_TRANSLATION
from formpack.schema.datadef import FormChoice, SharedChoiceOptions

COLORS = [('red', ['Red']), ('blue', ['Blue'])]


def test_versions_with_the_same_choices_share_one_list():
    pack = _pack(_schema('v1', COLORS), _schema('v2', COLORS))

    assert _options(pack, 'v1') is _options(pack, 'v2')


def test_unchanged_choices_stay_shared_when_another_choice_changes():
    changed = [('red', ['Red']), ('blue', ['Dark blue'])]
    pack = _pack(_schema('v1', COLORS), _schema('v2', changed))
    first, second = _options(pack, 'v1'), _options(pack, 'v2')

    assert first is not second
    assert first['red'] is second['red']
    assert first['blue'] is not second['blue']
    assert _labels(first['blue']) == ['Blue']
    assert _labels(second['blue']) == ['Dark blue']


def test_choices_with_the_same_label_keep_their_own_name():
    pack = _pack(_schema('v1', [('yes', ['Same']), ('no', ['Same'])]))
    options = _options(pack, 'v1')

    assert options['yes'] is not options['no']
    assert options['yes']['name'] == 'yes'
    assert options['no']['name'] == 'no'


def test_choice_that_returns_to_an_older_value_reuses_its_option():
    changed = [('red', ['Dark red']), ('blue', ['Blue'])]
    pack = _pack(
        _schema('v1', COLORS), _schema('v2', changed), _schema('v3', COLORS)
    )

    assert _options(pack, 'v1')['red'] is _options(pack, 'v3')['red']
    assert _labels(_options(pack, 'v2')['red']) == ['Dark red']


def test_same_choices_in_another_order_keep_their_own_order():
    reordered = [('blue', ['Blue']), ('red', ['Red'])]
    pack = _pack(_schema('v1', COLORS), _schema('v2', reordered))
    first, second = _options(pack, 'v1'), _options(pack, 'v2')

    assert first is not second
    assert list(first) == ['red', 'blue']
    assert list(second) == ['blue', 'red']
    assert first['red'] is second['red']


def test_removed_choice_does_not_reuse_the_longer_list():
    pack = _pack(_schema('v1', COLORS), _schema('v2', COLORS[:1]))

    assert list(_options(pack, 'v2')) == ['red']
    assert list(_options(pack, 'v1')) == ['red', 'blue']


def test_other_translations_do_not_share_an_option():
    pack = _pack(
        _schema('v1', [('red', ['Red'])], translations=['English (en)']),
        _schema('v2', [('red', ['Red'])], translations=['Anglais (en)']),
    )
    first, second = _options(pack, 'v1'), _options(pack, 'v2')

    assert first['red'] is not second['red']
    assert list(first['red']['labels']) == ['English (en)']
    assert list(second['red']['labels']) == ['Anglais (en)']


@pytest.mark.parametrize(
    'first_label, second_label',
    [(1, 1.0), (1, True), (1.0, True), (0, False)],
)
def test_labels_that_python_treats_as_equal_stay_distinct(
    first_label, second_label
):
    pack = _pack(
        _schema('v1', [('one', [first_label])]),
        _schema('v2', [('one', [second_label])]),
    )
    first, second = _options(pack, 'v1'), _options(pack, 'v2')

    assert first is not second
    assert first['one'] is not second['one']
    assert repr(_labels(first['one'])) == repr([first_label])
    assert repr(_labels(second['one'])) == repr([second_label])


def test_names_that_python_treats_as_equal_stay_distinct():
    shared_options = SharedChoiceOptions()

    first = shared_options.get_option(1, ['One'], (None,))
    second = shared_options.get_option(1.0, ['One'], (None,))

    assert first is not second
    assert repr(second['name']) == '1.0'


def test_label_that_cannot_be_hashed_keeps_its_own_option():
    labels = [['nested']]
    shared_options = SharedChoiceOptions()

    first = shared_options.get_option('one', labels, (None,))
    second = shared_options.get_option('one', labels, (None,))

    assert first is not second
    assert first == second


def test_a_definition_builds_without_shared_options():
    definition = [{'list_name': 'colors', 'name': 'red', 'label': ['Red']}]

    choices = FormChoice.all_from_json_definition(definition, [None])

    assert choices['colors'].options == {
        'red': {'labels': {None: 'Red'}, 'name': 'red'}
    }


def test_a_new_formpack_shares_nothing_with_another_one():
    first_pack = _pack(_schema('v1', COLORS))
    second_pack = _pack(_schema('v1', COLORS))

    assert _options(first_pack, 'v1') is not _options(second_pack, 'v1')
    assert _options(first_pack, 'v1')['red'] is not (
        _options(second_pack, 'v1')['red']
    )


def test_export_and_report_write_nothing_to_shared_options():
    """
    An export merges the choices of each field across the versions. Writing to
    a shared option or list would show up in every version that uses it.
    """

    changed = [('red', ['Dark red']), ('green', ['Green'])]
    pack = _pack(
        _schema('v1', COLORS),
        _schema('v2', COLORS),
        _schema('v3', changed),
        _schema('v4', changed),
    )
    lists = [_options(pack, version) for version in pack.versions]
    copies = [deepcopy(options) for options in lists]
    submissions = [
        {'__version__': 'v1', 'q1': 'red', 'q2': 'red blue'},
        {'__version__': 'v4', 'q1': 'green', 'q2': 'red green'},
    ]

    for _ in range(2):
        export = pack.export(
            versions=pack.versions.keys(),
            multiple_select='both',
            lang=UNSPECIFIED_TRANSLATION,
        )
        export.to_dict(deepcopy(submissions))
        report = pack.autoreport(versions=pack.versions.keys())
        list(report.get_stats(deepcopy(submissions)))

    assert lists == copies


def test_exports_stay_the_same_as_without_sharing(monkeypatch):
    schemas = [
        _schema('v1', COLORS),
        _schema('v2', [('red', ['Dark red']), ('blue', ['Blue'])]),
        _schema('v3', [('green', ['Green']), ('red', ['Dark red'])]),
        _schema('v4', [('green', ['Green']), ('red', ['Red'])]),
        _schema('v5', [('one', [1]), ('red', ['Red'])]),
        _schema('v6', [('one', [1.0]), ('red', ['Red'])]),
    ]
    submissions = [
        {'__version__': version, 'q1': 'red', 'q2': 'red'}
        for version in ('v1', 'v2', 'v3', 'v4', 'v5', 'v6')
    ]
    shared_pack = _pack(*deepcopy(schemas))

    monkeypatch.setattr(
        SharedChoiceOptions,
        'get_option',
        lambda self, name, labels, translations: self._build_option(
            name, labels, translations
        ),
    )
    monkeypatch.setattr(
        SharedChoiceOptions,
        'get_list',
        lambda self, list_name, options: options,
    )
    plain_pack = _pack(*deepcopy(schemas))
    assert _options(shared_pack, 'v2')['red'] is (
        _options(shared_pack, 'v3')['red']
    )
    assert _options(plain_pack, 'v2')['red'] is not (
        _options(plain_pack, 'v3')['red']
    )

    for multiple_select in ('both', 'summary', 'details'):
        exports = [
            pack.export(
                versions=pack.versions.keys(),
                multiple_select=multiple_select,
                lang=UNSPECIFIED_TRANSLATION,
            ).to_dict(deepcopy(submissions))
            for pack in (shared_pack, plain_pack)
        ]
        # A JSON dump also compares the order of the columns
        assert json.dumps(exports[0]) == json.dumps(exports[1])


def _labels(option):
    return list(option['labels'].values())


def _options(pack, version):
    section = pack.versions[version].sections[pack.title]
    return section.fields['q1'].choice.options


def _pack(*schemas):
    return FormPack(schemas, title='title', id_string='form')


def _schema(version, choices, translations=None):
    translations = translations or [None]
    return {
        'version': version,
        'content': {
            'schema': '1',
            'settings': {},
            'survey': [
                {
                    'type': type_,
                    'name': name,
                    'select_from_list_name': 'colors',
                    'label': [name for _ in translations],
                }
                for type_, name in (
                    ('select_one', 'q1'),
                    ('select_multiple', 'q2'),
                )
            ],
            'choices': [
                {'list_name': 'colors', 'name': name, 'label': label}
                for name, label in choices
            ],
            'translated': ['label'],
            'translations': translations,
        },
    }
