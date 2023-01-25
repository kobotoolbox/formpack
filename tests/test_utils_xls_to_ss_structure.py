from collections import OrderedDict

from formpack.utils.xls_to_ss_structure import xls_to_dicts, xlsx_to_dicts


def test_xls_to_dicts():
    with open('tests/fixtures/xlsforms/library-locking-example.xls', 'rb') as f:
        data = xls_to_dicts(f)
    assert list(data.keys()) == [
        'survey',
        'choices',
        'settings',
        'kobo--locking-profiles',
    ]
    expected_result = OrderedDict(
        [
            (
                'survey',
                [
                    OrderedDict(
                        [
                            ('type', 'select_one countries'),
                            ('name', 'country'),
                            ('label', 'Select your country'),
                            ('kobo--locking-profile', 'profile_1'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('type', 'select_one cities'),
                            ('name', 'city'),
                            ('label', 'Select your city'),
                            ('kobo--locking-profile', 'profile_2'),
                        ]
                    ),
                ],
            ),
            (
                'choices',
                [
                    OrderedDict(
                        [
                            ('list_name', 'countries'),
                            ('name', 'canada'),
                            ('label', 'Canada'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('list_name', 'countries'),
                            ('name', 'usa'),
                            ('label', 'United States of America'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('list_name', 'cities'),
                            ('name', 'vancouver'),
                            ('label', 'Vancouver'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('list_name', 'cities'),
                            ('name', 'toronto'),
                            ('label', 'Toronto'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('list_name', 'cities'),
                            ('name', 'baltimore'),
                            ('label', 'Baltimore'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('list_name', 'cities'),
                            ('name', 'boston'),
                            ('label', 'Boston'),
                        ]
                    ),
                ],
            ),
            (
                'settings',
                [
                    OrderedDict(
                        [
                            ('kobo--locking-profile', 'profile_3'),
                            ('kobo--lock_all', 'false'),
                            ('form_title', 'Library Locking'),
                        ]
                    )
                ],
            ),
            (
                'kobo--locking-profiles',
                [
                    OrderedDict(
                        [('restriction', 'choice_add'), ('profile_1', 'locked')]
                    ),
                    OrderedDict(
                        [
                            ('restriction', 'choice_delete'),
                            ('profile_2', 'locked'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('restriction', 'choice_label_edit'),
                            ('profile_1', 'locked'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('restriction', 'choice_order_edit'),
                            ('profile_1', 'locked'),
                            ('profile_2', 'locked'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('restriction', 'form_appearance'),
                            ('profile_3', 'locked'),
                        ]
                    ),
                ],
            ),
        ]
    )
    assert data == expected_result


def test_xlsx_to_dicts():
    with open(
        'tests/fixtures/xlsforms/library-locking-example.xlsx', 'rb'
    ) as f:
        data = xlsx_to_dicts(f)
    assert list(data.keys()) == [
        'survey',
        'choices',
        'settings',
        'kobo--locking-profiles',
    ]
    expected_result = OrderedDict(
        [
            (
                'survey',
                [
                    OrderedDict(
                        [
                            ('type', 'select_one countries'),
                            ('name', 'country'),
                            ('label', 'Select your country'),
                            ('kobo--locking-profile', 'profile_1'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('type', 'select_one cities'),
                            ('name', 'city'),
                            ('label', 'Select your city'),
                            ('kobo--locking-profile', 'profile_2'),
                        ]
                    ),
                ],
            ),
            (
                'choices',
                [
                    OrderedDict(
                        [
                            ('list_name', 'countries'),
                            ('name', 'canada'),
                            ('label', 'Canada'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('list_name', 'countries'),
                            ('name', 'usa'),
                            ('label', 'United States of America'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('list_name', 'cities'),
                            ('name', 'vancouver'),
                            ('label', 'Vancouver'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('list_name', 'cities'),
                            ('name', 'toronto'),
                            ('label', 'Toronto'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('list_name', 'cities'),
                            ('name', 'baltimore'),
                            ('label', 'Baltimore'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('list_name', 'cities'),
                            ('name', 'boston'),
                            ('label', 'Boston'),
                        ]
                    ),
                ],
            ),
            (
                'settings',
                [
                    OrderedDict(
                        [
                            ('kobo--locking-profile', 'profile_3'),
                            ('kobo--lock_all', 'false'),
                            ('form_title', 'Library Locking'),
                        ]
                    )
                ],
            ),
            (
                'kobo--locking-profiles',
                [
                    OrderedDict(
                        [('restriction', 'choice_add'), ('profile_1', 'locked')]
                    ),
                    OrderedDict(
                        [
                            ('restriction', 'choice_delete'),
                            ('profile_2', 'locked'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('restriction', 'choice_label_edit'),
                            ('profile_1', 'locked'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('restriction', 'choice_order_edit'),
                            ('profile_1', 'locked'),
                            ('profile_2', 'locked'),
                        ]
                    ),
                    OrderedDict(
                        [
                            ('restriction', 'form_appearance'),
                            ('profile_3', 'locked'),
                        ]
                    ),
                ],
            ),
        ]
    )
    assert data == expected_result
