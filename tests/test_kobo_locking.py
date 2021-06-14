# coding: utf-8

import base64
from io import BytesIO
from unittest import TestCase

import xlwt

from formpack.constants import KOBO_LOCK_SHEET
from formpack.utils.kobo_locking import (
    get_kobo_locking_profiles,
    revert_kobo_lock_structure,
    strip_kobo_locking_profile,
)
from formpack.utils.exceptions import FormPackLibraryLockingError


class TestKoboLocking(TestCase):
    def setUp(self):
        self.locking_profiles = [
            ['restriction', 'core', 'flex', 'delete'],
            ['choice_add', 'locked', 'locked', ''],
            ['choice_delete', '', '', 'locked'],
            ['choice_value_edit', '', '', ''],
            ['choice_label_edit', '', '', ''],
            ['choice_order_edit', 'locked', '', ''],
            ['question_delete', 'locked', 'locked', 'locked'],
            ['question_label_edit', 'locked', 'locked', ''],
            ['question_settings_edit', 'locked', 'locked', ''],
            ['question_skip_logic_edit', 'locked', 'locked', ''],
            ['question_validation_edit', 'locked', 'locked', ''],
            ['group_delete', 'locked', '', 'locked'],
            ['group_label_edit', '', '', ''],
            ['group_question_add', 'locked', 'locked', ''],
            ['group_question_delete', 'locked', 'locked', 'locked'],
            ['group_question_order_edit', 'locked', 'locked', ''],
            ['group_settings_edit', 'locked', 'locked', ''],
            ['group_skip_logic_edit', 'locked', 'locked', ''],
            ['group_split', 'locked', 'locked', ''],
            ['form_replace', 'locked', '', ''],
            ['group_add', 'locked', '', ''],
            ['question_add', 'locked', '', ''],
            ['question_order_edit', 'locked', '', ''],
            ['language_edit', 'locked', '', ''],
            ['form_appearance', 'locked', '', ''],
            ['form_meta_edit', '', '', ''],
        ]

    def _construct_xls_for_import(self, sheet_name, sheet_content):
        workbook_to_import = xlwt.Workbook()
        worksheet = workbook_to_import.add_sheet(sheet_name)
        for row_num, row_list in enumerate(sheet_content):
            for col_num, cell_value in enumerate(row_list):
                worksheet.write(row_num, col_num, cell_value)
        xls_import_io = BytesIO()
        workbook_to_import.save(xls_import_io)
        xls_import_io.seek(0)
        return xls_import_io

    def test_get_kobo_locking_profiles(self):
        expected_locking_profiles = [
            {
                'name': 'core',
                'restrictions': [
                    'choice_add',
                    'choice_order_edit',
                    'question_delete',
                    'question_label_edit',
                    'question_settings_edit',
                    'question_skip_logic_edit',
                    'question_validation_edit',
                    'group_delete',
                    'group_question_add',
                    'group_question_delete',
                    'group_question_order_edit',
                    'group_settings_edit',
                    'group_skip_logic_edit',
                    'group_split',
                    'form_replace',
                    'group_add',
                    'question_add',
                    'question_order_edit',
                    'language_edit',
                    'form_appearance',
                ],
            },
            {
                'name': 'delete',
                'restrictions': [
                    'choice_delete',
                    'question_delete',
                    'group_delete',
                    'group_question_delete',
                ],
            },
            {
                'name': 'flex',
                'restrictions': [
                    'choice_add',
                    'question_delete',
                    'question_label_edit',
                    'question_settings_edit',
                    'question_skip_logic_edit',
                    'question_validation_edit',
                    'group_question_add',
                    'group_question_delete',
                    'group_question_order_edit',
                    'group_settings_edit',
                    'group_skip_logic_edit',
                    'group_split',
                ],
            },
        ]

        xls = self._construct_xls_for_import(
            KOBO_LOCK_SHEET, self.locking_profiles
        )
        actual_locking_profiles = get_kobo_locking_profiles(xls)
        for profiles in expected_locking_profiles:
            name = profiles['name']
            expected_restrictions = profiles['restrictions']
            actual_restrictions = [
                val['restrictions']
                for val in actual_locking_profiles
                if val['name'] == name
            ][0]
            assert expected_restrictions == actual_restrictions

    def test_revert_kobo_lock_structure(self):
        expected_reverted_locking_profiles = [
            {'restriction': 'choice_add', 'core': 'locked', 'flex': 'locked'},
            {'restriction': 'choice_delete', 'delete': 'locked'},
            {'restriction': 'choice_label_edit'},
            {'restriction': 'choice_value_edit'},
            {'restriction': 'choice_order_edit', 'core': 'locked'},
            {
                'restriction': 'question_delete',
                'core': 'locked',
                'flex': 'locked',
                'delete': 'locked',
            },
            {
                'restriction': 'question_label_edit',
                'core': 'locked',
                'flex': 'locked',
            },
            {
                'restriction': 'question_settings_edit',
                'core': 'locked',
                'flex': 'locked',
            },
            {
                'restriction': 'question_skip_logic_edit',
                'core': 'locked',
                'flex': 'locked',
            },
            {
                'restriction': 'question_validation_edit',
                'core': 'locked',
                'flex': 'locked',
            },
            {
                'restriction': 'group_delete',
                'core': 'locked',
                'delete': 'locked',
            },
            {
                'restriction': 'group_split',
                'core': 'locked',
                'flex': 'locked',
            },
            {'restriction': 'group_label_edit'},
            {
                'restriction': 'group_question_add',
                'core': 'locked',
                'flex': 'locked',
            },
            {
                'restriction': 'group_question_delete',
                'core': 'locked',
                'flex': 'locked',
                'delete': 'locked',
            },
            {
                'restriction': 'group_question_order_edit',
                'core': 'locked',
                'flex': 'locked',
            },
            {
                'restriction': 'group_settings_edit',
                'core': 'locked',
                'flex': 'locked',
            },
            {
                'restriction': 'group_skip_logic_edit',
                'core': 'locked',
                'flex': 'locked',
            },
            {'restriction': 'form_replace', 'core': 'locked'},
            {'restriction': 'group_add', 'core': 'locked'},
            {'restriction': 'question_add', 'core': 'locked'},
            {'restriction': 'question_order_edit', 'core': 'locked'},
            {'restriction': 'language_edit', 'core': 'locked'},
            {'restriction': 'form_appearance', 'core': 'locked'},
            {'restriction': 'form_meta_edit'},
        ]
        xls = self._construct_xls_for_import(
            KOBO_LOCK_SHEET, self.locking_profiles
        )
        actual_reverted_locks = {
            KOBO_LOCK_SHEET: get_kobo_locking_profiles(xls)
        }
        revert_kobo_lock_structure(actual_reverted_locks)

        def _get_sorted_restrictions(restrictions):
            return sorted(restrictions, key=lambda k: k['restriction'])

        actual = _get_sorted_restrictions(
            actual_reverted_locks[KOBO_LOCK_SHEET]
        )
        expected = _get_sorted_restrictions(expected_reverted_locking_profiles)
        assert len(actual) == len(expected)
        assert actual == expected

    def test_strip_kobo_locks_from_survey_content(self):
        content = {
            'survey': [
                {
                    'name': 'today',
                    'type': 'today',
                    '$kuid': 'pitYOxYwh',
                    '$autoname': 'today',
                },
                {
                    'name': 'gender',
                    'type': 'select_one',
                    '$kuid': '6bPK3a1G1',
                    'label': ["Respondent's gender?"],
                    'required': True,
                    '$autoname': 'gender',
                    'kobo--locking-profile': 'flex',
                    'select_from_list_name': 'gender',
                },
                {
                    'name': 'age',
                    'type': 'integer',
                    '$kuid': 'Ms8NYWNpT',
                    'label': ["Respondent's age?"],
                    'required': True,
                    '$autoname': 'age',
                },
                {
                    'name': 'confirm',
                    'type': 'select_one',
                    '$kuid': 'SBHBly6cC',
                    'label': ['Is your age really ${age}?'],
                    'relevant': '${age}!=' '',
                    'required': True,
                    '$autoname': 'confirm',
                    'kobo--locking-profile': 'delete',
                    'select_from_list_name': 'yesno',
                },
                {
                    'name': 'group_1',
                    'type': 'begin_group',
                    '$kuid': 'pUGHAi9Wv',
                    'label': ['A message from our sponsors'],
                    '$autoname': 'group_1',
                    'kobo--locking-profile': 'core',
                },
                {
                    'name': 'note_1',
                    'type': 'note',
                    '$kuid': 'KXV08ZVMS',
                    'label': ['Hi there 👋'],
                    '$autoname': 'note_1',
                },
                {'type': 'end_group', '$kuid': '04eEDul2R'},
            ]
        }
        strip_kobo_locking_profile(content)
        for item in content['survey']:
            assert 'kobo--locking-profile' not in item

    def test_no_locking_profiles_raises_exception(self):
        no_profiles = [[row[0]] for row in self.locking_profiles]
        xls = self._construct_xls_for_import(
            KOBO_LOCK_SHEET, no_profiles
        )
        try:
            get_kobo_locking_profiles(xls)
        except FormPackLibraryLockingError as e:
            assert str(e) == 'At least one locking profile must be defined.'

    def test_locking_profile_name_is_locked_raises_exception(self):
        locking_profiles = self.locking_profiles
        locking_profiles[0][1] = 'locked'
        xls = self._construct_xls_for_import(
            KOBO_LOCK_SHEET, locking_profiles
        )
        try:
            get_kobo_locking_profiles(xls)
        except FormPackLibraryLockingError as e:
            assert str(e) == 'Locking profile name of "locked" cannot be used.'

    def test_invalid_restriction_raises_exception(self):
        locking_profiles = self.locking_profiles
        locking_profiles.append(['invalid_restriction', 'locked', 'locked', 'locked'])
        xls = self._construct_xls_for_import(
            KOBO_LOCK_SHEET, locking_profiles
        )
        try:
            get_kobo_locking_profiles(xls)
        except FormPackLibraryLockingError as e:
            assert str(e) == 'invalid_restriction is not a valid restriction.'

    def test_restriction_column_missing_raises_exception(self):
        locking_profiles = self.locking_profiles
        locking_profiles[0][0] = 'something_other_than_restriction'
        xls = self._construct_xls_for_import(
            KOBO_LOCK_SHEET, locking_profiles
        )
        try:
            get_kobo_locking_profiles(xls)
        except FormPackLibraryLockingError as e:
            assert str(e) == 'The column name `restriction` must be present.'

