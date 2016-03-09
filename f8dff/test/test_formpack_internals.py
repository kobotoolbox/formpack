import unittest
from f8dff.models.formpack.pack import FormPack


class TestInternalMethods(unittest.TestCase):
    def test_lookup(self):
        fp = FormPack(title='fptitle')
        self.assertEqual(fp.lookup('title'), 'fptitle')

    def test_lookup_none_val(self):
        fp = FormPack(title=None)
        self.assertEqual(fp.lookup('title', 'notnone'), 'notnone')
