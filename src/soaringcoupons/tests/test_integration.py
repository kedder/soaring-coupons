# -*- coding: utf-8 -*-

import doctest
import webtest
import webapp2

from google.appengine.ext import testbed

def doctest_home():
    """
        >>> app = create_testapp()
        >>> resp = app.get('/')
        >>> resp.status
        '200 OK'

        >>> 'Soaring Coupons' in resp
        True
    """

def create_testapp():
    config = {'webtopay_project_id': 'test',
              'webtopay_password': 'pass',
              'debug': False}
    from soaringcoupons.main import routes
    app = webapp2.WSGIApplication(routes=routes,
                                  debug=config['debug'],
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
