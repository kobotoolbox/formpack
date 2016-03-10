import unittest
from f8dff.models.formpack.pack import FormPack
from f8dff.fixtures import build_fixture

restaurant_profile = build_fixture('restaurant_profile')


class TestInternalMethods(unittest.TestCase):
    def test_lookup(self):
        fp = FormPack(title='fptitle')
        self.assertEqual(fp.lookup('title'), 'fptitle')

    def test_lookup_none_val(self):
        fp = FormPack(title=None)
        self.assertEqual(fp.lookup('title', 'notnone'), 'notnone')


class TestSurveyParsers(unittest.TestCase):
    def test_fixture_has_languages(self):
        '''
        restauraunt_profile@v2 has two languages
        '''

        fp = FormPack(**restaurant_profile)
        self.assertEqual(len(fp.versions[1].languages), 2)
