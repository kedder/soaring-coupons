# -*- coding: utf-8 -*-
import unittest
from datetime import datetime

from soaringcoupons import formatters
class FormattersTestCase(unittest.TestCase):
    def test_format_yesno(self):
        self.assertEqual(formatters.format_yesno(True), u'Taip')

        self.assertEqual(formatters.format_yesno(False), u'Ne')

        self.assertEqual(formatters.format_yesno(None), u'Ne')

        self.assertEqual(formatters.format_yesno('Hello'), u'Taip')

    def test_format_date(self):
        dt = datetime(2012, 12, 28, 13, 43)
        self.assertEqual(formatters.format_date(dt), '2012-12-28')

        self.assertEqual(formatters.format_date(None), '')

    def test_format_datetime(self):
        dt = datetime(2012, 12, 28, 13, 43)
        self.assertEqual(formatters.format_datetime(dt), '2012-12-28 13:43')
        self.assertEqual(formatters.format_datetime(None), '')
