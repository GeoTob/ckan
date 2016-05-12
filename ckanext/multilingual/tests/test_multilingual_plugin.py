import ckan.plugins as p
import ckanext.multilingual.plugin as mulilingual_plugin
import ckan.lib.helpers
import ckan.lib.create_test_data
import ckan.logic.action.update
import ckan.model as model
import ckan.tests.legacy
import ckan.tests.legacy.html_check
import routes
import paste.fixture
import pylons.test

_create_test_data = ckan.lib.create_test_data


class TestDatasetTermTranslation(ckan.tests.legacy.html_check.HtmlCheckMethods):
    'Test the translation of datasets by the multilingual_dataset plugin.'
    @classmethod
    def setup(cls):
        cls.app = paste.fixture.TestApp(pylons.test.pylonsapp)

        if not p.plugin_loaded('multilingual_dataset'):
            p.load('multilingual_dataset')

        if not p.plugin_loaded('multilingual_group'):
            p.load('multilingual_group')

        if not p.plugin_loaded('multilingual_tag'):
            p.load('multilingual_tag')
        ckan.tests.legacy.setup_test_search_index()
        _create_test_data.CreateTestData.create_translations_test_data()

        cls.sysadmin_user = model.User.get('testsysadmin')
        cls.org = {'name': 'test_org',
                   'title': 'russian',
                   'description': 'Roger likes these books.'}
        ckan.tests.legacy.call_action_api(cls.app, 'organization_create',
                                          apikey=cls.sysadmin_user.apikey,
                                          **cls.org)
        dataset = {'name': 'test_org_dataset',
                   'title': 'A Novel By Tolstoy',
                   'owner_org': cls.org['name']}
        ckan.tests.legacy.call_action_api(cls.app, 'package_create',
                                          apikey=cls.sysadmin_user.apikey,
                                          **dataset)

        # Add translation terms that match a couple of group names and package
        # names. Group names and package names should _not_ get translated even
        # if there are terms matching them, because they are used to form URLs.
        for term in ('roger', 'david', 'annakarenina', 'warandpeace'):
            for lang_code in ('en', 'de', 'fr'):
                data_dict = {'term': term,
                             'term_translation': 'this should not be rendered',
                             'lang_code': lang_code}
                context = {'model': ckan.model,
                           'session': ckan.model.Session,
                           'user': 'testsysadmin'}
                ckan.logic.action.update.term_translation_update(
                    context, data_dict)

    @classmethod
    def teardown(cls):
        p.unload('multilingual_dataset')
        p.unload('multilingual_group')
        p.unload('multilingual_tag')
        ckan.model.repo.rebuild_db()
        ckan.lib.search.clear_all()

    def test_user_read_translation(self):
        '''Test the translation of datasets on user view pages by the
        multilingual_dataset plugin.

        '''

        # It is testsysadmin who created the dataset, so testsysadmin whom
        # we'd expect to see the datasets for.
        for user_name in ('testsysadmin',):
            offset = routes.url_for(
                controller='user', action='read', id=user_name)
            for (lang_code, translations) in (
                    ('de', _create_test_data.german_translations),
                    ('fr', _create_test_data.french_translations),
                    ('en', _create_test_data.english_translations),
                    ('pl', {})):
                response = self.app.get(
                    offset,
                    status=200,
                    extra_environ={'CKAN_LANG': lang_code,
                                   'CKAN_CURRENT_URL': offset})
                terms = ('A Novel By Tolstoy')
                for term in terms:
                    if term in translations:
                        assert translations[term] in response, response
                    elif term in _create_test_data.english_translations:
                        assert (_create_test_data.english_translations[term]
                                in response)
                    else:
                        assert term in response
                assert 'this should not be rendered' not in response

    def test_org_read_translation(self):
        for (lang_code, translations) in (
                ('de', _create_test_data.german_translations),
                ('fr', _create_test_data.french_translations),
                ('en', _create_test_data.english_translations),
                ('pl', {})):
            offset = '/{0}/organization/{1}'.format(
                lang_code, self.org['name'])
            response = self.app.get(offset, status=200)
            terms = ('A Novel By Tolstoy',
                     'russian',
                     'Roger likes these books.')
            for term in terms:
                if term in translations:
                    assert translations[term] in response
                elif term in _create_test_data.english_translations:
                    assert (_create_test_data.english_translations[term]
                            in response)
                else:
                    assert term in response
            assert 'this should not be rendered' not in response

    def test_org_index_translation(self):
        for (lang_code, translations) in (
                ('de', _create_test_data.german_translations),
                ('fr', _create_test_data.french_translations),
                ('en', _create_test_data.english_translations),
                ('pl', {})):
            offset = '/{0}/organization'.format(lang_code)
            response = self.app.get(offset, status=200)
            for term in ('russian', 'Roger likes these books.'):
                if term in translations:
                    assert translations[term] in response
                elif term in _create_test_data.english_translations:
                    assert (_create_test_data.english_translations[term]
                            in response)
                else:
                    assert term in response, response
            assert ('/{0}/organization/{1}'.format(lang_code, self.org['name'])
                    in response)
            assert 'this should not be rendered' not in response


class TestDatasetSearchIndex():

    @classmethod
    def setup_class(cls):

        if not p.plugin_loaded('multilingual_dataset'):
            p.load('multilingual_dataset')

        if not p.plugin_loaded('multilingual_group'):
            p.load('multilingual_group')

        data_dicts = [
            {'term': 'moo',
             'term_translation': 'french_moo',
             'lang_code': 'fr'},
            {'term': 'moo',
             'term_translation': 'this should not be rendered',
             'lang_code': 'fsdas'},
            {'term': 'an interesting note',
             'term_translation': 'french note',
             'lang_code': 'fr'},
            {'term': 'moon',
             'term_translation': 'french moon',
             'lang_code': 'fr'},
            {'term': 'boon',
             'term_translation': 'french boon',
             'lang_code': 'fr'},
            {'term': 'boon',
             'term_translation': 'italian boon',
             'lang_code': 'it'},
            {'term': 'david',
             'term_translation': 'french david',
             'lang_code': 'fr'},
            {'term': 'david',
             'term_translation': 'italian david',
             'lang_code': 'it'}
        ]

        context = {
            'model': ckan.model,
            'session': ckan.model.Session,
            'user': 'testsysadmin',
            'ignore_auth': True,
        }
        for data_dict in data_dicts:
            ckan.logic.action.update.term_translation_update(
                context, data_dict)

    @classmethod
    def teardown(cls):
        p.unload('multilingual_dataset')
        p.unload('multilingual_group')
        ckan.model.repo.rebuild_db()
        ckan.lib.search.clear_all()

    def test_translate_terms(self):

        sample_index_data = {
            'download_url': u'moo',
            'notes': u'an interesting note',
            'tags': [u'moon', 'boon'],
            'title': u'david',
        }

        result = mulilingual_plugin.MultilingualDataset().before_index(
            sample_index_data)

        assert result == {
            'text_pl': '',
            'text_de': '',
            'text_ro': '',
            'title': u'david',
            'notes': u'an interesting note',
            'tags': [u'moon', 'boon'],
            'title_en': u'david',
            'download_url': u'moo',
            'text_it': u'italian boon',
            'text_es': '',
            'text_en': u'an interesting note moon boon moo',
            'text_nl': '',
            'title_it': u'italian david',
            'text_pt': '',
            'title_fr': u'french david',
            'text_fr': u'french note french boon french_moo french moon'
        }, result
