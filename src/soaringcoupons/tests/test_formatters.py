# -*- coding: utf-8 -*-

import doctest
from datetime import datetime

from soaringcoupons import formatters

def doctest_format_yesno():
    """
        >>> formatters.format_yesno(True)
        u'Taip'

        >>> formatters.format_yesno(False)
        u'Ne'

        >>> formatters.format_yesno(None)
        u'Ne'

        >>> formatters.format_yesno('Hello')
        u'Taip'
    """

def doctest_format_date():
    """
        >>> dt = datetime(2012, 12, 28, 13, 43)
        >>> formatters.format_date(dt)
        '2012-12-28'

        >>> formatters.format_date(None)
        ''
    """

def doctest_format_datetime():
    """
        >>> dt = datetime(2012, 12, 28, 13, 43)
        >>> formatters.format_datetime(dt)
        '2012-12-28 13:43'

        >>> formatters.format_datetime(None)
        ''
    """

DOCTEST_OPTION_FLAGS = (doctest.NORMALIZE_WHITESPACE|
                        doctest.ELLIPSIS|
                        doctest.REPORT_ONLY_FIRST_FAILURE|
                        doctest.REPORT_NDIFF
                        )
def test_suite():
    return doctest.DocTestSuite(optionflags=DOCTEST_OPTION_FLAGS)

