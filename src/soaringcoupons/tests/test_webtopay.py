import doctest

from soaringcoupons import webtopay

def doctest_tst():
    """
        >>> 2+2
        4
    """

def doctest_buildrequest():
    """
        >>> data = {'orderid': '123',
        ...         'accepturl': 'http://local.test/accept',
        ...         'cancelurl': 'http://local.test/cancel',
        ...         'callbackurl': 'http://local.test/callback',
        ...         'sign_password': 'asdfghjkl'
        ...         }
        >>> webtopay.build_request(data)
    """

DOCTEST_OPTION_FLAGS = (doctest.NORMALIZE_WHITESPACE|
                        doctest.ELLIPSIS|
                        doctest.REPORT_ONLY_FIRST_FAILURE|
                        doctest.REPORT_NDIFF
                        )
def test_suite():
    return doctest.DocTestSuite(optionflags=DOCTEST_OPTION_FLAGS)
