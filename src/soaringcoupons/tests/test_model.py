# -*- coding: utf-8 -*-

import doctest
import datetime
import random

import mock
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util

from soaringcoupons import model

class FakeDateTime(datetime.datetime):
    @classmethod
    def now(self):
        return datetime.datetime(2012, 1, 4)

def doctest_order_gen_id():
    """
    Mock random.choice to return always '0'
        >>> x = mock.patch('datetime.datetime', FakeDateTime).start()

        >>> x = mock.patch('random.choice').start()
        >>> random.choice.return_value = '0'

        >>> model.order_gen_id()
        '121000000'
        >>> model.order_gen_id()
        '122000000'
        >>> model.order_gen_id()
        '123000000'
    """

def doctest_order_create():
    """
        >>> ct = model.CouponType('test', 300.0, "Test flight")
        >>> order = model.order_create(model.order_gen_id(), ct, test=True)

        >>> order.coupon_type
        'test'
        >>> order.price
        300.0
        >>> order.status == model.Order.ST_PENDING
        True
        >>> order.currency
        'LTL'
        >>> order.create_time
        datetime.datetime(...)
    """

def doctest_order_cancel():
    """
    Create order

        >>> ct = model.CouponType('test', 300.0, "Test flight")
        >>> order = model.order_create(model.order_gen_id(), ct, test=True)

    Cancelling order changes its status
        >>> cancelled = model.order_cancel(order.key().name())
        >>> cancelled.status == model.Order.ST_CANCELLED
        True

    You cannot cancel already cancelled order
        >>> model.order_cancel(order.key().name())
        Traceback (most recent call last):
        ...
        ValueError: Cannot cancel non-pending order ...

"""

def doctest_order_process():
    """
    Create sample order

        >>> ct = model.CouponType('test', 300.0, "Test flight")
        >>> order = model.order_create('1', ct, test=True)

    Process successful payment

        >>> order, coupon = model.order_process(order.order_id,
        ...                                     'test@test.com', 100.0, 'EUR',
        ...                                     payer_name='Andrey',
        ...                                     payer_surname='Lebedev',
        ...                                     payment_provider='dnb')
        >>> order.status == model.Order.ST_PAID
        True
        >>> order.payer_name
        'Andrey'
        >>> order.payer_surname
        'Lebedev'
        >>> order.payer_email
        u'test@test.com'
        >>> order.payment_time != None
        True
        >>> order.paid_amount
        100.0
        >>> order.paid_currency
        'EUR'

    Check created coupon
        >>> coupon.order is not None
        True
        >>> coupon.order == order
        True
        >>> coupon.status == model.Coupon.ST_ACTIVE
        True
        >>> coupon.use_time
        >>> coupon.key().name()
        u'1'

    Make sure coupon is in database
        >>> model.coupon_get('1').key() == coupon.key()
        True
    """

def doctest_order_process_twice():
    """
    Create sample order

        >>> ct = model.CouponType('test', 300.0, "Test flight")
        >>> order = model.order_create('2', ct, test=True)

    Process successful payment

        >>> order, coupon = model.order_process(order.order_id,
        ...                                     'test@test.com', 100.0, 'EUR',
        ...                                     payer_name='Andrey',
        ...                                     payer_surname='Lebedev',
        ...                                     payment_provider='dnb')

    Attempt to process payment second time and expect the exception
        >>> model.order_process(order.order_id, 'test@test.com', 100.0, 'EUR')
        Traceback (most recent call last):
        ...
        ValueError: Cannot process non-pending order ...


    """

def doctest_counter():
    """ Naive test for counter

        >>> model.counter_next()
        1L
        >>> model.counter_next()
        2L
        >>> model.counter_next()
        3L
        >>> model.counter_next()
        4L
        >>> model.counter_next()
        5L
        >>> model.counter_next()
        6L
    """

def setUp(test):
    test.testbed = testbed.Testbed()
    test.testbed.activate()
    policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=0)
    test.testbed.init_datastore_v3_stub(consistency_policy=policy)

def tearDown(test):
    test.testbed.deactivate()
    mock.patch.stopall()

DOCTEST_OPTION_FLAGS = (doctest.NORMALIZE_WHITESPACE|
                        doctest.ELLIPSIS|
                        doctest.REPORT_ONLY_FIRST_FAILURE|
                        doctest.REPORT_NDIFF
                        )
def test_suite():
    return doctest.DocTestSuite(setUp=setUp, tearDown=tearDown,
                                optionflags=DOCTEST_OPTION_FLAGS)
