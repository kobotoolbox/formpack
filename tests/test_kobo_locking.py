# coding: utf-8

import base64
from io import BytesIO
from unittest import TestCase

import xlwt

from formpack.constants import KOBO_LOCK_SHEET
from formpack.utils.kobo_locking import (
    get_kobo_locking_profiles,
    revert_kobo_lock_structre,
)


class TestKoboLocking(TestCase):
    def setUp(self):
        self.locking_profiles = [
            ['restriction', 'core', 'flex', 'delete'],
            ['choice_add', True, True, ''],
            ['choice_delete', '', '', True],
            ['choice_edit', '', '', ''],
            ['choice_order_edit', True, '', ''],
            ['question_delete', True, True, True],
            ['question_label_edit', True, True, ''],
            ['question_settings_edit', True, True, ''],
            ['question_skip_logic_edit', True, True, ''],
            ['question_validation_edit', True, True, ''],
            ['group_delete', True, '', True],
            ['group_label_edit', '', '', ''],
            ['group_question_add', True, True, ''],
            ['group_question_delete', True, True, True],
            ['group_question_order_edit', True, True, ''],
            ['group_settings_edit', True, True, ''],
            ['group_skip_logic_edit', True, True, ''],
            ['form_replace', True, '', ''],
            ['group_add', True, '', ''],
            ['question_add', True, '', ''],
            ['question_order_edit', True, '', ''],
            ['translations_manage', True, '', ''],
            ['form_appearance', True, '', ''],
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
                    'form_replace',
                    'group_add',
                    'question_add',
                    'question_order_edit',
                    'translations_manage',
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

    def test_revert_kobo_lock_structre(self):
        expected_reverted_locking_profiles = [
            {'restriction': 'choice_add', 'core': True, 'flex': True},
            {'restriction': 'choice_delete', 'delete': True},
            {'restriction': 'choice_edit'},
            {'restriction': 'choice_order_edit', 'core': True},
            {
                'restriction': 'question_delete',
                'core': True,
                'flex': True,
                'delete': True,
            },
            {
                'restriction': 'question_label_edit',
                'core': True,
                'flex': True,
            },
            {
                'restriction': 'question_settings_edit',
                'core': True,
                'flex': True,
            },
            {
                'restriction': 'question_skip_logic_edit',
                'core': True,
                'flex': True,
            },
            {
                'restriction': 'question_validation_edit',
                'core': True,
                'flex': True,
            },
            {'restriction': 'group_delete', 'core': True, 'delete': True},
            {'restriction': 'group_label_edit'},
            {
                'restriction': 'group_question_add',
                'core': True,
                'flex': True,
            },
            {
                'restriction': 'group_question_delete',
                'core': True,
                'flex': True,
                'delete': True,
            },
            {
                'restriction': 'group_question_order_edit',
                'core': True,
                'flex': True,
            },
            {
                'restriction': 'group_settings_edit',
                'core': True,
                'flex': True,
            },
            {
                'restriction': 'group_skip_logic_edit',
                'core': True,
                'flex': True,
            },
            {'restriction': 'form_replace', 'core': True},
            {'restriction': 'group_add', 'core': True},
            {'restriction': 'question_add', 'core': True},
            {'restriction': 'question_order_edit', 'core': True},
            {'restriction': 'translations_manage', 'core': True},
            {'restriction': 'form_appearance', 'core': True},
        ]
        xls = self._construct_xls_for_import(
            KOBO_LOCK_SHEET, self.locking_profiles
        )
        actual_reverted_locks = {
            KOBO_LOCK_SHEET: get_kobo_locking_profiles(xls)
        }
        revert_kobo_lock_structre(actual_reverted_locks)

        def _get_sorted_restrictions(restrictions):
            return sorted(restrictions, key=lambda k:k['restriction'])

        actual = _get_sorted_restrictions(
            actual_reverted_locks[KOBO_LOCK_SHEET]
        )
        expected = _get_sorted_restrictions(
            expected_reverted_locking_profiles
        )
        assert len(actual) == len(expected)
        assert actual == expected

