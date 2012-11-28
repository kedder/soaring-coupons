import doctest
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
        {'data': 'b3JkZXJpZD0xMjMmc29tZS1vdGhlci1wYXJhbWV0ZXI9YWJjJnByb2plY3RpZD0xMjMmYW1vdW50PTEwMCZ2ZXJzaW9uPTEuNiZjYW5jZWx1cmw9aHR0cCUzQSUyRiUyRmxvY2FsLnRlc3QlMkYmYWNjZXB0dXJsPWh0dHAlM0ElMkYlMkZsb2NhbC50ZXN0JTJGJmNhbGxiYWNrdXJsPWh0dHAlM0ElMkYlMkZsb2NhbC50ZXN0JTJG',
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

DOCTEST_OPTION_FLAGS = (doctest.NORMALIZE_WHITESPACE|
                        doctest.ELLIPSIS|
                        doctest.REPORT_ONLY_FIRST_FAILURE|
                        doctest.REPORT_NDIFF
                        )
def test_suite():
    return doctest.DocTestSuite(optionflags=DOCTEST_OPTION_FLAGS)
