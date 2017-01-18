# -*- coding: utf-8 -*-
import unittest
import base64

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

    @mock.patch('soaringcoupons.mailgun.send_mail')
    def test_callback_success(self, send_mail_mock):
        # Create test order

        ct = model.CouponType('test', 200.0, 'Test coupon')
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
        self.assertEqual(len(send_mail_mock.mock_calls), 1)

        # Make sure email contains correct link to coupon
        msg = send_mail_mock.mock_calls[0][2]
        msg_contents = msg['body']
        self.assertRegexpMatches(msg_contents, r'http://.*/coupon/1001')

    def test_accept(self):
        # We need to see results of order_process immediately in this test
        self.cpolicy.SetProbability(1.0)

        ct = model.CouponType('test', 200.0, 'Test coupon')
        order = model.order_create('1', ct)
        with mock.patch('soaringcoupons.model.coupon_gen_id') as m:
            m.return_value = '1001'
            order, coupons = model.order_process(order.order_id,
                                                 'test@test.com', 200.0, 'LTL')

        # load "accept" url
        app = create_testapp()
        resp = app.get('/accept/1')
        self.assertIn('<a href="/coupon/1001"', resp)

    @mock.patch('soaringcoupons.mailgun.send_mail')
    def test_spawn(self, send_mail_mock):
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
        self.assertEqual(len(send_mail_mock.mock_calls), 10)

    def test_order(self):
        app = create_testapp()
        self.cpolicy.SetProbability(1.0)

        resp = app.post('/order/acro')
        self.assertEqual(resp.status, '302 Moved Temporarily')

        location = resp.headers['Location']
        self.assertTrue(location.startswith("https://www.mokejimai.lt/pay/"))

        # Make sure there is an order registered
        orders = list(model.Order.all())
        self.assertEqual(len(orders), 1)

        order = orders[0]
        self.assertEqual(order.is_paid(), False)
        self.assertEqual(order.currency, "EUR")
        self.assertEqual(order.price, 90.0)
        self.assertEqual(order.status, model.Order.ST_PENDING)
        self.assertEqual(order.quantity, 1)
        self.assertEqual(order.test, False)

    def test_coupon(self):
        # Make sure coupon page is generated with all registered coupon types
        app = create_testapp()

        for idx, ct in enumerate(model.coupon_types):
            order = model.order_create(str(idx), ct)
            coupons = model.coupon_create(order)

            self.assertEquals(len(coupons), 1)
            cid = coupons[0].coupon_id
            resp = app.get('/coupon/%s' % cid)

            self.assertIn(cid, resp)

    def test_coupon_unknown_type(self):
        # Make sure we fail if we try to generate coupon for unknown type
        app = create_testapp()

        ct = model.CouponType('test', 200.0, 'Test coupon')
        order = model.order_create("1", ct)
        coupons = model.coupon_create(order)
        self.assertEquals(len(coupons), 1)
        cid = coupons[0].coupon_id

        # Let's pretend coupon_type test is a registered type
        with mock.patch('soaringcoupons.model.get_coupon_type') as m:
            m.return_value = ct
            with self.assertRaises(webtest.AppError):
                app.get('/coupon/%s' % cid)

    def test_qr(self):
        app = create_testapp()

        ct = model.get_coupon_type("plane_long")
        order = model.order_create("1", ct)
        coupons = model.coupon_create(order)
        self.assertEquals(len(coupons), 1)
        cid = coupons[0].coupon_id
        resp = app.get("/qr/%s" % cid)

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(resp.headers['Content-Type'], 'image/png')
        self.assertEqual(resp.body[:4], '\x89PNG')

    def test_admin_list(self):
        app = create_testapp()
        self.cpolicy.SetProbability(1.0)

        # Pre-generate some coupons
        ct = model.get_coupon_type("plane_long")
        order = model.order_create("1", ct)
        model.coupon_create(order)

        model.coupon_spawn(model.get_coupon_type("training"), 3,
                           "test@example.com", "test")

        resp = app.get("/admin/list")
        self.assertEqual(resp.status, "200 OK")
        self.assertIn("react-content", resp)

    def test_admin_check(self):
        app = create_testapp()
        self.cpolicy.SetProbability(1.0)

        ct = model.get_coupon_type("plane_long")
        order = model.order_create("1", ct)
        coupons = model.coupon_create(order)
        cid = coupons[0].coupon_id

        resp = app.get("/admin/check/%s" % cid)

        self.assertEqual(resp.status, "200 OK")
        self.assertIn("Kvietimas galioja.", resp)

    def test_admin_check_use(self):
        app = create_testapp()
        self.cpolicy.SetProbability(1.0)

        ct = model.get_coupon_type("plane_long")
        order = model.order_create("1", ct)
        coupons = model.coupon_create(order)
        cid = coupons[0].coupon_id

        resp = app.post("/admin/check/%s" % cid)
        self.assertEqual(resp.status, "302 Moved Temporarily")

        used = model.coupon_get(cid)
        self.assertEqual(used.status, model.Coupon.ST_USED)

    def test_dashboard(self):
        app = create_testapp()
        self.cpolicy.SetProbability(1.0)

        # Pre-generate some coupons
        ct = model.get_coupon_type("plane_long")
        order = model.order_create("1", ct)
        model.coupon_create(order)

        model.coupon_spawn(model.get_coupon_type("training"), 3,
                           "test@example.com", "test")

        resp = app.get("/admin")
        self.assertEqual(resp.status, "200 OK")
        self.assertIn("Statistika", resp)

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        self.cpolicy = PseudoRandomHRConsistencyPolicy(probability=0)
        self.testbed.init_datastore_v3_stub(consistency_policy=self.cpolicy)

        self.testbed.init_user_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()


def create_testapp():
    config = {'webtopay_project_id': 'test',
              'webtopay_password': 'pass',
              'home_url': None,
              'mailgun_domain': '-',
              'mailgun_apikey': '-',
              'debug': False}
    app = webapp2.WSGIApplication(routes=controller.get_routes(),
                                  debug=True,
                                  config=config)
    return webtest.TestApp(app)


