import unittest
from ..models.formpack.pack import FormPack
from ..fixtures import build_fixture

restaurant_profile = build_fixture('restaurant_profile')


class TestInternalMethods(unittest.TestCase):
    def test_lookup(self):
        fp = FormPack(title='fptitle')
        self.assertEqual(fp.lookup('title'), 'fptitle')

    def test_lookup_none_val(self):
        fp = FormPack(title=None)
        self.assertEqual(fp.lookup('title', 'notnone'), 'notnone')


class TestSurveyParsers(unittest.TestCase):
    def test_fixture_has_translations(self):
        '''
        restauraunt_profile@v2 has two translations
        '''

        fp = FormPack(**restaurant_profile)
        self.assertEqual(len(fp[1].translations), 2)
