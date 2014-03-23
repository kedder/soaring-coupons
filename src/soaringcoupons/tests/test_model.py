# -*- coding: utf-8 -*-
import unittest
import datetime
from contextlib import contextmanager

import mock
from google.appengine.ext import testbed
from google.appengine.datastore.datastore_stub_util import \
    PseudoRandomHRConsistencyPolicy

from soaringcoupons import model


class ModelTestCase(unittest.TestCase):

    def test_coupon_gen_id(self):
        with mock.patch("random.choice", return_value="0"):
            with freeze_time(datetime.datetime(2012, 1, 4)):
                self.assertEqual(model.coupon_gen_id(), '121000000')
                self.assertEqual(model.coupon_gen_id(), '122000000')
                self.assertEqual(model.coupon_gen_id(), '123000000')

    def test_order_create(self):
        ct = model.CouponType('test', 300.0, "Test flight")
        order = model.order_create(model.order_gen_id(), ct, test=True)

        self.assertEqual(order.coupon_type, 'test')
        self.assertEqual(order.price, 300.0)
        self.assertEqual(order.status == model.Order.ST_PENDING, True)
        self.assertEqual(order.currency, 'LTL')
        self.assertIsNotNone(order.create_time)

    def test_order_cancel(self):
        # Create order
        ct = model.CouponType('test', 300.0, "Test flight")
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
        ct = model.CouponType('test', 300.0, "Test flight")
        order = model.order_create('1', ct, test=True)

        # Process successful payment
        order, coupons = model.order_process(order.order_id,
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
        self.assertEqual(len(coupons), 1)
        coupon = coupons[0]
        self.assertIsNotNone(coupon.order)
        self.assertIs(coupon.order, order)
        self.assertEqual(coupon.status, model.Coupon.ST_ACTIVE)
        self.assertIsNone(coupon.use_time)
        cid = coupon.coupon_id
        self.assertEqual(len(cid), 9)

        # Make sure coupon is in database
        self.assertEqual(model.coupon_get(cid).key(), coupon.key())

    def test_order_process_twice(self):
        # Create sample order

        ct = model.CouponType('test', 300.0, "Test flight")
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

    def test_order_find_coupons(self):
        # We need to see results of order_process immediately in this test
        self.cpolicy.SetProbability(1.0)

        # Create two orders and process successful payment
        ct = model.CouponType('test', 300.0, "Test flight")
        order1 = model.order_create('1', ct, test=True)
        model.order_process(order1.order_id, 'test@test.com', 100.0, 'EUR')
        order2 = model.order_create('2', ct, test=True)
        model.order_process(order2.order_id, 'test@test.com', 100.0, 'EUR')

        coupons = model.order_find_coupons(order1.order_id)
        self.assertEqual(len(coupons), 1)

        self.assertEqual(coupons[0].order.order_id, order1.order_id)

    def test_coupon_search(self):
        self.cpolicy.SetProbability(1.0)

        ct = model.CouponType('test', 300.0, "Test flight")

        with freeze_time(datetime.datetime(2013, 2, 16)):
            order1 = model.order_create('1', ct, test=True)
            model.order_process(order1.order_id, 'test@test.com', 100.0, 'EUR')

        with freeze_time(datetime.datetime(2013, 12, 31)):
            order2 = model.order_create('2', ct, test=True)
            o, coupons = model.order_process(order2.order_id, 'test@test.com',
                                             100.0, 'EUR')
            model.coupon_use(coupons[0].coupon_id)

        with freeze_time(datetime.datetime(2014, 1, 11)):
            order2 = model.order_create('3', ct, test=True)
            model.order_process(order2.order_id, 'test@test.com', 100.0, 'EUR')

    def test_order_count_by_status(self):
        self.cpolicy.SetProbability(1.0)

        def neworder(status, test=False):
            o = model.Order(status=status,
                            price=300.0,
                            create_time=datetime.datetime.now(),
                            coupon_type="test",
                            test=test)
            o.put()

        # Create some orders
        neworder(model.Order.ST_PENDING)
        neworder(model.Order.ST_PENDING)
        neworder(model.Order.ST_PENDING)

        neworder(model.Order.ST_PAID)
        neworder(model.Order.ST_PAID)

        neworder(model.Order.ST_SPAWNED)
        neworder(model.Order.ST_SPAWNED, test=True)
        neworder(model.Order.ST_SPAWNED, test=True)

        # Calculate statistics
        stats = model.order_count_by_status()

        # Verify stats
        self.assertEqual(stats,
                         {model.Order.ST_SPAWNED: 1,
                          model.Order.ST_PAID: 2})

    def test_coupon_count_by_type(self):
        self.cpolicy.SetProbability(1.0)

        def newcoupon(type, test=False):
            o = model.Order(status=model.Order.ST_PAID,
                            price=300.0,
                            create_time=datetime.datetime.now(),
                            coupon_type=type,
                            test=test)
            o.put()
            c = model.Coupon(order=o,
                             status=model.Coupon.ST_ACTIVE,
                             )
            c.put()

        newcoupon("training")
        newcoupon("training")
        newcoupon("acro")
        newcoupon("acro", test=True)

        # Calculate statistics
        stats = model.coupon_count_by_type()

        # Verify stats
        self.assertEqual(stats,
                         {"training": 2,
                          "acro": 1})

    def test_counter(self):
        # Naive test for counter
        self.assertEqual(model.counter_next(), 1)
        self.assertEqual(model.counter_next(), 2)
        self.assertEqual(model.counter_next(), 3)
        self.assertEqual(model.counter_next(), 4)
        self.assertEqual(model.counter_next(), 5)
        self.assertEqual(model.counter_next(), 6)

    def test_spawn_coupons(self):
        ct = model.CouponType('test', 300.0, "Test flight")
        coupons = model.coupon_spawn(ct, 4,
                                     email="test@test.com",
                                     notes="2% parama")
        self.assertEqual(len(coupons), 4)
        c1 = coupons[0]
        order = c1.order
        self.assertTrue(c1.active)
        self.assertIsNotNone(order)
        self.assertEqual(order.quantity, 4)
        self.assertIsNotNone(order.payment_time)

        # make sure all coupon ids are different
        coupon_ids = [c.coupon_id for c in coupons]
        self.assertEqual(len(set(coupon_ids)), 4)

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.cpolicy = PseudoRandomHRConsistencyPolicy(probability=0)
        self.testbed.init_datastore_v3_stub(consistency_policy=self.cpolicy)

    def tearDown(self):
        self.testbed.deactivate()
        mock.patch.stopall()


@contextmanager
def freeze_time(dt):
    real_date = datetime.date
    real_datetime = datetime.datetime

    class FakeDateType(type):
        def __instancecheck__(self, instance):
            return isinstance(instance, real_date)

    class FakeDate(real_date):
        __metaclass__ = FakeDateType

        def __new__(cls, *args, **kwargs):
            return real_date.__new__(real_date, *args, **kwargs)

        @staticmethod
        def today():
            return dt.date()

    class FakeDateTime(real_datetime):
        def __new__(cls, *args, **kwargs):
            return real_datetime.__new__(real_datetime, *args, **kwargs)

        @staticmethod
        def now():
            return dt

    date_patch = mock.patch("datetime.date", FakeDate)
    datetime_patch = mock.patch("datetime.datetime", FakeDateTime)
    with date_patch, datetime_patch:
        yield
