# -*- coding: utf-8 -*-

import doctest
import urllib

import webtest
import webapp2
from google.appengine.ext import testbed

from soaringcoupons import controller, webtopay, model

def doctest_home():
    """
        >>> app = create_testapp()
        >>> resp = app.get('/')
        >>> resp.status
        '200 OK'

        >>> 'Soaring Coupons' in resp
        True
    """

def doctest_callback():
    """
    Create test order

        >>> ct = model.CouponType('test', 200.0, 'Test coupon')
        >>> order = model.order_create('1', ct)

    Prepare request as webtopay would
        >>> req = {'orderid': '1',
        ...        'payamount': '20000',
        ...        'paycurrency': 'LTL',
        ...        'p_email': 'test@test.com',
        ...        'name': 'Bill',
        ...        'surename': 'Gates',
        ...        'payment': 'test'}
        >>> data = webtopay._safe_base64_encode(
        ...                 webtopay._prepare_query_string(req, 'test'))
        >>> signature = webtopay._sign(data, 'pass')

        >>> app = create_testapp()
        >>> params = {'data': data, 'ss1': signature}
        >>> resp = app.get('/callback', params=params)
        >>> resp.body
        'OK'


    """

def create_testapp():
    config = {'webtopay_project_id': 'test',
              'webtopay_password': 'pass',
              'debug': False}
    app = webapp2.WSGIApplication(routes=controller.get_routes(),
                                  debug=True,
                                  config=config)
    return webtest.TestApp(app)


def setUp(test):
    test.testbed = testbed.Testbed()
    test.testbed.activate()
    test.testbed.init_datastore_v3_stub()

def tearDown(test):
    test.testbed.deactivate()

DOCTEST_OPTION_FLAGS = (doctest.NORMALIZE_WHITESPACE|
                        doctest.ELLIPSIS|
                        doctest.REPORT_ONLY_FIRST_FAILURE|
                        doctest.REPORT_NDIFF
                        )
def test_suite():
    return doctest.DocTestSuite(setUp=setUp, tearDown=tearDown,
                                optionflags=DOCTEST_OPTION_FLAGS)
