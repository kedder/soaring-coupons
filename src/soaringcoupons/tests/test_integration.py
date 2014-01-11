# -*- coding: utf-8 -*-
import unittest

import webtest
import webapp2
import mock
from google.appengine.ext import testbed
from google.appengine.datastore.datastore_stub_util import \
    PseudoRandomHRConsistencyPolicy

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
        with mock.patch('soaringcoupons.model.coupon_gen_id') as m:
            m.return_value = '1001'
            resp = app.get('/callback', params=params)

        self.assertEqual(resp.body, 'OK')

        # Check order status
        order = model.order_get('1')
        self.assertEqual(order.status, model.Order.ST_PAID)

        # Check coupon status
        coupon = model.coupon_get('1001')
        self.assertNotEqual(coupon, None)
        self.assertEqual(coupon.status, model.Coupon.ST_ACTIVE)

        # Make sure email was sent
        messages = self.mail_stub.get_sent_messages()
        self.assertEqual(len(messages), 1)

        # Make sure email contains correct link to coupon
        self.assertRegexpMatches(messages[0].body.payload,
                                 r'http://.*/coupon/1001')

    def test_accept(self):
        # We need to see results of order_process immediately in this test
        self.cpolicy.SetProbability(1.0)

        ct = model.CouponType('test', 200.0, 'Test coupon', 'Test coupon')
        order = model.order_create('1', ct)
        with mock.patch('soaringcoupons.model.coupon_gen_id') as m:
            m.return_value = '1001'
            order, coupons = model.order_process(order.order_id,
                                                 'test@test.com', 200.0, 'LTL')

        # load "accept" url
        app = create_testapp()
        resp = app.get('/accept/1')
        self.assertIn('<a href="/coupon/1001"', resp)

    def test_spawn(self):
        app = create_testapp()
        resp = app.get('/admin/spawn')
        self.assertEqual(resp.status, '200 OK')

        # submit with empty fields
        resp = app.post('/admin/spawn', {})
        self.assertEqual(resp.status, '200 OK')
        self.assertIn('This field is required.', resp.body)

        # email validation works
        resp = app.post('/admin/spawn', {'email': 'hello@wiorld@gmail.com'})
        self.assertEqual(resp.status, '200 OK')
        self.assertIn('Invalid e-mail address.', resp.body)

        # submit correct fields
        data = {'coupon_type': 'acro',
                'email': 'test@test.com',
                'count': '10',
                'notes': '2%'}

        resp = app.post('/admin/spawn', data)
        self.assertEqual(resp.status, '302 Moved Temporarily')

        # Make sure emails are sent out
        messages = self.mail_stub.get_sent_messages()
        self.assertEqual(len(messages), 10)
        self.assertEqual(messages[0].to, 'test@test.com')

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        self.cpolicy = PseudoRandomHRConsistencyPolicy(probability=0)
        self.testbed.init_datastore_v3_stub(consistency_policy=self.cpolicy)

        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

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


