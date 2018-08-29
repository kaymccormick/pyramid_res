from pyramid.config import Configurator
from pyramid.paster import setup_logging, get_appsettings

from tests.testing import MyTestCase
from webtest import TestApp


class MyWebTestCase(MyTestCase):
    config_uri = 'testing.ini'

    def wsgi_app(self):
        config_uri = self.config_uri

        setup_logging(config_uri)
        settings = get_appsettings(config_uri)
        config = self.config = self.configurator(settings=settings)
        return config.make_wsgi_app()

    def webtest_app(self):
        self.app = self.wsgi_app()
        return TestApp(self.app)

    def setUp(self):
        super().setUp()

    def test_include(self):
        self.config = self.configurator(self.settings)
        self.config.include('pyramid_res')
        self.test_app = self.webtest_app()
        pass

    def configurator(self, settings):
        config = Configurator(settings=settings)
        return config