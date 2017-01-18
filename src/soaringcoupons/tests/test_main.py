# -*- coding: utf-8 -*-
import unittest

from google.appengine.ext import testbed

from soaringcoupons import model, controller


class MainTest(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_initial_run(self):
        # On the first startup, application is unconfigured, so only one
        # handler is present, that should guide the configuration.
        from soaringcoupons import main
        app = main.make_app()

        self.assertIsNotNone(app)

        self.assertEqual(len(app.router.match_routes), 1)

        route = app.router.match_routes[0]
        self.assertIs(route.handler, controller.UnconfiguredHandler)

    def test_configured_run(self):
        # When application is configured, all the handlers are present
        settings_entity = model.Settings.get_or_insert("test")
        settings_entity.webtopay_project_id = "test"
        settings_entity.put()
        self.assertTrue(settings_entity.is_configured())

        from soaringcoupons import main
        app = main.make_app()

        self.assertIsNotNone(app)
        self.assertEqual(len(app.router.match_routes), 14)
