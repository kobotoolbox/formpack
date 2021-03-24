# coding: utf-8

import base64
from io import BytesIO
from unittest import TestCase

import xlrd
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
        expected_content_kobo_locks = [
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

    def _construct_xls_for_import(self, sheet_name, sheet_content):
        # Construct a binary XLS file that we'll import later
        wb = Workbook()
        sheet = wb.active
        sheet.title = sheet_name
        for i, row in enumerate(sheet_content):
            for j, value in enumerate(row):
                sheet.cell(column=j+1, row=i+1, value=value)
        x = BytesIO()
        wb.save(x)
        x.seek(0)
        encoded_xls = base64.b64encode(x.read())
        return encoded_xls

    def test_get_kobo_locking_profiles(self):
        xls = self._construct_xls_for_import(
            'kobo--locking-profiles', self.locking_profiles
        )
        get_kobo_locking_profiles(BytesIO(xls))

