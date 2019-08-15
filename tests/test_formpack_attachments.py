# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest
from formpack.b64_attachment import B64Attachment

from .fixtures.load_fixture_json import load_fixture_json


class TestB64Attachment(unittest.TestCase):
    def test_string_matches(self):
        expectations = [
            ['data:image/png;base64,wxyz', True],
            ['data:image/jpeg;base64,xyz', True],
            ['abcdefghijklmnopqrstuvwxyz', False],
        ]
        for item_str, tf in expectations:
            self.assertEqual(B64Attachment._is_attachment(item_str), tf)

    def test_extensions(self):
        expectations = [
            ['data:image/png;base64,wxyz', 'image', 'png'],
            ['data:image/jpeg;base64,xyz', 'image', 'jpeg'],
        ]
        for item_str, exp_mtype, exp_ext in expectations:
            (mtype, ext, contents) = B64Attachment._attachment_split(item_str)
            self.assertEqual(exp_ext, ext)
            self.assertEqual(exp_mtype, mtype)

    def test_write_to_file(self):
        img_example = load_fixture_json('restaurant_photo/images')[0]
        attachment = B64Attachment(img_example)
        (filename, filepath,) = B64Attachment.write_to_tempfile(attachment)
        self.assertTrue(len(filename) > 1)
        self.assertTrue(len(filepath) > 1)
