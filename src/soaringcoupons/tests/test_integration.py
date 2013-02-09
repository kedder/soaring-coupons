# -*- coding: utf-8 -*-
import unittest

import webtest
import webapp2
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util

from soaringcoupons import controller, webtopay, model

class IntegrationTestCase(unittest.TestCase):
    def test_home(self):
        app = create_testapp()
        resp = app.get('/')
        self.assertEqual(resp.status, '200 OK')
        self.assertTrue(u'Pramoginiai skrydžiai' in resp)

    def test_callback_success(self):
        # Create test order

        ct = model.CouponType('test', 200.0, 'Test coupon', 'Test coupon')
        order = model.order_create('1', ct)

        # Prepare request as webtopay would
        req = {'orderid': '1',
               'payamount': '20000',
               'paycurrency': 'LTL',
               'p_email': 'test@test.com',
               'status': '1',
               'name': 'Bill',
               'surename': 'Gates',
               'payment': 'test'}
        data = webtopay._safe_base64_encode(
                        webtopay._prepare_query_string(req, 'test'))
        signature = webtopay._sign(data, 'pass')

        app = create_testapp()
        params = {'data': data, 'ss1': signature}
        resp = app.get('/callback', params=params)
        self.assertEqual(resp.body, 'OK')

        # Check order status

        order = model.order_get('1')
        self.assertEqual(order.status, model.Order.ST_PAID)

        # Chcek coupon status
        coupon = model.coupon_get('1')
        self.assertNotEqual(coupon, None)
        self.assertEqual(coupon.status, model.Coupon.ST_ACTIVE)

        # Make sure email was sent
        messages = self.mail_stub.get_sent_messages()
        self.assertEqual(len(messages), 1)


    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=0)
        self.testbed.init_datastore_v3_stub(consistency_policy=policy)

        self.testbed.init_mail_stub()
        self.mail_stub= self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

        self.testbed.init_user_stub()

    def tearDown(self):
        self.testbed.deactivate()


def create_testapp():
    config = {'webtopay_project_id': 'test',
              'webtopay_password': 'pass',
              'home_url': None,
              'debug': False}
    app = webapp2.WSGIApplication(routes=controller.get_routes(),
                                  debug=True,
                                  config=config)
    return webtest.TestApp(app)


