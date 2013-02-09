# -*- coding: utf-8 -*-
import unittest
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

class ModelTestCase(unittest.TestCase):

    def test_order_gen_id(self):
        # Mock random.choice to return always '0'
        mock.patch('datetime.datetime', FakeDateTime).start()
        mock.patch('random.choice').start()
        random.choice.return_value = '0'

        self.assertEqual(model.order_gen_id(), '121000000')
        self.assertEqual(model.order_gen_id(), '122000000')
        self.assertEqual(model.order_gen_id(), '123000000')

    def test_order_create(self):
        ct = model.CouponType('test', 300.0, "Test flight", "Test flight")
        order = model.order_create(model.order_gen_id(), ct, test=True)

        self.assertEqual(order.coupon_type, 'test')
        self.assertEqual(order.price, 300.0)
        self.assertEqual(order.status == model.Order.ST_PENDING, True)
        self.assertEqual(order.currency, 'LTL')
        self.assertIsNotNone(order.create_time)

    def test_order_cancel(self):
        # Create order
        ct = model.CouponType('test', 300.0, "Test flight", "Test flight")
        order = model.order_create(model.order_gen_id(), ct, test=True)

        # Cancelling order changes its status
        cancelled = model.order_cancel(order.key().name())
        self.assertEqual(cancelled.status, model.Order.ST_CANCELLED)

        # You cannot cancel already cancelled order
        with self.assertRaisesRegexp(ValueError,
                                     r'Cannot cancel non-pending order .*'):
            model.order_cancel(order.key().name())


    def test_order_process(self):
        # Create sample order
        ct = model.CouponType('test', 300.0, "Test flight", "Test flight")
        order = model.order_create('1', ct, test=True)

        # Process successful payment

        order, coupon = model.order_process(order.order_id,
                                            'test@test.com', 100.0, 'EUR',
                                            payer_name='Andrey',
                                            payer_surname='Lebedev',
                                            payment_provider='dnb')
        self.assertEqual(order.status, model.Order.ST_PAID)
        self.assertEqual(order.payer_name, 'Andrey')
        self.assertEqual(order.payer_surname, 'Lebedev')
        self.assertEqual(order.payer_email, u'test@test.com')
        self.assertIsNotNone(order.payment_time)
        self.assertEqual(order.paid_amount, 100.0)
        self.assertEqual(order.paid_currency, 'EUR')

        # Check created coupon
        self.assertIsNotNone(coupon.order)
        self.assertIs(coupon.order, order)
        self.assertEqual(coupon.status, model.Coupon.ST_ACTIVE)
        self.assertIsNone(coupon.use_time)
        self.assertEqual(coupon.key().name(), u'1')

        # Make sure coupon is in database
        self.assertEqual(model.coupon_get('1').key(), coupon.key())

    def test_order_process_twice(self):
        # Create sample order

        ct = model.CouponType('test', 300.0, "Test flight", "Test flight")
        order = model.order_create('2', ct, test=True)

        # Process successful payment

        order, coupon = model.order_process(order.order_id,
                                            'test@test.com', 100.0, 'EUR',
                                            payer_name='Andrey',
                                            payer_surname='Lebedev',
                                            payment_provider='dnb')

        # Attempt to process payment second time and expect the exception
        with self.assertRaisesRegexp(ValueError,
                                     r'Cannot process non-pending order .*'):
            model.order_process(order.order_id, 'test@test.com', 100.0, 'EUR')

    def test_counter(self):
        # Naive test for counter
        self.assertEqual(model.counter_next(), 1)
        self.assertEqual(model.counter_next(), 2)
        self.assertEqual(model.counter_next(), 3)
        self.assertEqual(model.counter_next(), 4)
        self.assertEqual(model.counter_next(), 5)
        self.assertEqual(model.counter_next(), 6)

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=0)
        self.testbed.init_datastore_v3_stub(consistency_policy=policy)

    def tearDown(self):
        self.testbed.deactivate()
        mock.patch.stopall()
