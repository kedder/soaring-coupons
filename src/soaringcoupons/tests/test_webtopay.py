import doctest
import mock
from pprint import pprint

from soaringcoupons import webtopay

def doctest_build_request_no_projectid():
    """ Exception should be thrown if project id is not given

        >>> data = {'orderid': '123',
        ...         'accepturl': 'http://local.test/accept',
        ...         'cancelurl': 'http://local.test/cancel',
        ...         'callbackurl': 'http://local.test/callback',
        ...         'sign_password': 'asdfghjkl'
        ...         }
        >>> webtopay.build_request(data)
        Traceback (most recent call last):
        ...
        WebToPayException: sign_password or projectid is not provided
    """

def doctest_build_request():
    """
        >>> rq = webtopay.build_request({'projectid': '123',
        ...                              'sign_password': 'secret',
        ...                              'orderid': 123,
        ...                              'accepturl': 'http://local.test/',
        ...                              'cancelurl': 'http://local.test/',
        ...                              'callbackurl': 'http://local.test/',
        ...                              'amount': 100,
        ...                              'some-other-parameter': 'abc'})
        >>> pprint(rq)
        {'data': 'b3JkZXJpZD0xMjMmc29tZS...dHAlM0ElMkYlMkZsb2NhbC50ZXN0JTJG',
         'sign': '7461dff3e05d67d6e19e4c1021ce6163'}

    """

def doctest_prepare_query_string():
    """

        >>> data = {'orderid': 123,
        ...         'accepturl': 'http://local.test/',
        ...         'cancelurl': 'http://local.test/',
        ...         'callbackurl': 'http://local.test/',
        ...         'amount': 100,
        ...         'some-other-parameter': 'abc'}
        >>> qs = webtopay._prepare_query_string(data, '123')

        >>> expected = ('orderid=123&accepturl=http%3A%2F%2Flocal.test%2F'
        ...             '&cancelurl=http%3A%2F%2Flocal.test%2F'
        ...             '&callbackurl=http%3A%2F%2Flocal.test%2F&amount=100'
        ...             '&some-other-parameter=abc&version=1.6&projectid=123')


    Expected and produced query strings should be the same

        >>> import urlparse
        >>> pprint(urlparse.parse_qs(expected))
        {'accepturl': ['http://local.test/'],
         'amount': ['100'],
         'callbackurl': ['http://local.test/'],
         'cancelurl': ['http://local.test/'],
         'orderid': ['123'],
         'projectid': ['123'],
         'some-other-parameter': ['abc'],
         'version': ['1.6']}

        >>> pprint(urlparse.parse_qs(qs))
        {'accepturl': ['http://local.test/'],
         'amount': ['100'],
         'callbackurl': ['http://local.test/'],
         'cancelurl': ['http://local.test/'],
         'orderid': ['123'],
         'projectid': ['123'],
         'some-other-parameter': ['abc'],
         'version': ['1.6']}

    """

def doctest_response(self):
    """
        >>> import urlparse

        >>> qs = ('data=b3JkZXJpZD0xJmxhbmc9bGl0JnByb2plY3RpZD0zMDQzMiZjdXJyZ'
        ...       'W5jeT1MVEwmYW1vdW50PTMwMDAwJnZlcnNpb249MS42JmNvdW50cnk9TFQ'
        ...       'mdGVzdD0xJnR5cGU9RU1BJnBheW1lbnQ9aGFuemEmcGF5dGV4dD1VJUM1J'
        ...       'UJFc2FreW1hcytuciUzQSsxK2h0dHAlM0ElMkYlMkZ3d3cuc2tsYW5keW1'
        ...       'hcy5sdCtwcm9qZWt0ZS4rJTI4UGFyZGF2JUM0JTk3amFzJTNBK0RhbGlhK'
        ...       '1ZhaW5pZW4lQzQlOTclMjkmcF9lbWFpbD1hbmRyZXkubGViZWRldiU0MGd'
        ...       'tYWlsLmNvbSZwX2NvdW50cnluYW1lPSZzdGF0dXM9MSZyZXF1ZXN0aWQ9M'
        ...       'zQ0NjM5ODQmbmFtZT1VQUImc3VyZW5hbWU9TW9rJUM0JTk3amltYWkubHQ'
        ...       'mcGF5YW1vdW50PTMwMDAwJnBheWN1cnJlbmN5PUxUTA%3D%3D&ss1=e450'
        ...       'da330163deb38ec21ecc601c7125&ss2=B1AqKhD0nycSYhKvc60cYQvhs'
        ...       '-HPUt4r4kP7KrKOe77TVtg6G7GvRMhZ5fXruMPlDkg_ia2EqhGYzYGLQrj'
        ...       'EL2H2Db5_UiKKQSSqwrjE_Kka1h-mYVl6_ulM43uz87MQeYwh3DMRhoHx3'
        ...       'uih6Q3QqvqXypLY1tXZN2sDHFJIFGQ%3D')

        >>> qsplain = urlparse.unquote(qs)
        >>> data = dict(urlparse.parse_qsl(qsplain))
        >>> request = webtopay.validate_and_parse_data(data,
        ...                                            'badproject', 'badsig')
        Traceback (most recent call last):
        ...
        WebToPayException: Signature ss1 is not valid

    Mock signature checker to test parsing

        >>> with mock.patch('soaringcoupons.webtopay._is_valid_ss1') as m:
        ...    m.return_value = True
        ...    request = webtopay.validate_and_parse_data(data, '21', '')
        Traceback (most recent call last):
        ...
        WebToPayException_Callback: Bad project id: 30432, should be: 21

        >>> with mock.patch('soaringcoupons.webtopay._is_valid_ss1') as m:
        ...    m.return_value = True
        ...    request = webtopay.validate_and_parse_data(data, '30432', '')
        >>> pprint(request)
        {'amount': u'30000',
         'country': u'LT',
         'currency': u'LTL',
         'lang': u'lit',
         'name': u'UAB',
         'orderid': u'1',
         'p_email': u'andrey...@gmail.com',
         'payamount': u'30000',
         'paycurrency': u'LTL',
         'payment': u'hanza',
         'paytext': u'U\u017esakymas nr: 1 http://www.sklandymas.lt projekte.
                     (Pardav\u0117jas: ...)',
         'projectid': u'30432',
         'requestid': u'34463984',
         'status': u'1',
         'surename': u'Mok\u0117jimai.lt',
         'test': u'1',
         'type': 'macro',
         'version': u'1.6'}
        """

DOCTEST_OPTION_FLAGS = (doctest.NORMALIZE_WHITESPACE|
                        doctest.ELLIPSIS|
                        doctest.REPORT_ONLY_FIRST_FAILURE|
                        doctest.REPORT_NDIFF
                        )
def test_suite():
    return doctest.DocTestSuite(optionflags=DOCTEST_OPTION_FLAGS)
