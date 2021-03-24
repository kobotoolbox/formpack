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
            ['choice_add', 'true', 'true', ''],
            ['choice_delete', '', '', 'true'],
            ['choice_edit', '', '', ''],
            ['choice_order_edit', 'true', '', ''],
            ['question_delete', 'true', 'true', 'true'],
            ['question_label_edit', 'true', 'true', ''],
            ['question_settings_edit', 'true', 'true', ''],
            ['question_skip_logic_edit', 'true', 'true', ''],
            ['question_validation_edit', 'true', 'true', ''],
            ['group_delete', 'true', '', 'true'],
            ['group_label_edit', '', '', ''],
            ['group_question_add', 'true', 'true', ''],
            ['group_question_delete', 'true', 'true', 'true'],
            ['group_question_order_edit', 'true', 'true', ''],
            ['group_settings_edit', 'true', 'true', ''],
            ['group_skip_logic_edit', 'true', 'true', ''],
            ['form_replace', 'true', '', ''],
            ['group_add', 'true', '', ''],
            ['question_add', 'true', '', ''],
            ['question_order_edit', 'true', '', ''],
            ['translations_manage', 'true', '', ''],
            ['form_appearance', 'true', '', ''],
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
            {'restriction': 'choice_add', 'core': 'true', 'flex': 'true'},
            {'restriction': 'choice_delete', 'delete': 'true'},
            {'restriction': 'choice_edit'},
            {'restriction': 'choice_order_edit', 'core': 'true'},
            {
                'restriction': 'question_delete',
                'core': 'true',
                'flex': 'true',
                'delete': 'true',
            },
            {
                'restriction': 'question_label_edit',
                'core': 'true',
                'flex': 'true',
            },
            {
                'restriction': 'question_settings_edit',
                'core': 'true',
                'flex': 'true',
            },
            {
                'restriction': 'question_skip_logic_edit',
                'core': 'true',
                'flex': 'true',
            },
            {
                'restriction': 'question_validation_edit',
                'core': 'true',
                'flex': 'true',
            },
            {'restriction': 'group_delete', 'core': 'true', 'delete': 'true'},
            {'restriction': 'group_label_edit'},
            {
                'restriction': 'group_question_add',
                'core': 'true',
                'flex': 'true',
            },
            {
                'restriction': 'group_question_delete',
                'core': 'true',
                'flex': 'true',
                'delete': 'true',
            },
            {
                'restriction': 'group_question_order_edit',
                'core': 'true',
                'flex': 'true',
            },
            {
                'restriction': 'group_settings_edit',
                'core': 'true',
                'flex': 'true',
            },
            {
                'restriction': 'group_skip_logic_edit',
                'core': 'true',
                'flex': 'true',
            },
            {'restriction': 'form_replace', 'core': 'true'},
            {'restriction': 'group_add', 'core': 'true'},
            {'restriction': 'question_add', 'core': 'true'},
            {'restriction': 'question_order_edit', 'core': 'true'},
            {'restriction': 'translations_manage', 'core': 'true'},
            {'restriction': 'form_appearance', 'core': 'true'},
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

