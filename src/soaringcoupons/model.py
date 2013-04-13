# -*- coding: utf-8 -*-
import datetime
import random
import string
import logging
import textwrap
from collections import namedtuple, defaultdict

from google.appengine.ext import db

class CouponType(object):
    id = None
    price = None
    t = None

    def __init__(self, id, price, description=None):
        self.id = id
        self.price = price
        self.description = description


CouponType = namedtuple('CouponType', ['id', 'price', 'title', 'description'])

coupon_types = [CouponType('training', 150.0,
                           u'Apžvalginis skrydis sklandytuvu',
                           textwrap.dedent(u"""
                                           Sklandytuvas išvelkamas
                                           autoišvilktuvu ir maždaug 300 m.
                                           aukštyje atkabinamas.  Pakilę su
                                           patyrusiu pilotu, virš aerodromo
                                           apsuksite apžvalginį ratą. Skrydis
                                           truks apie 5 min.
                                           """)
                           ),
                CouponType('acro', 300.0,
                           u'Pilotavimo skrydis sklandytuvu',
                           textwrap.dedent(u"""
                                           Sklandytuvas išvelkamas lėktuvu
                                           ir aerodromo rajone atkabinamas.
                                           Skrisdami su patyrusiu pilotu,
                                           pasigrožėsite gamta , susipažinsite
                                           su sklandytuvo skrydžio galimybėmis,
                                           pamėginsite patys pilotuoti. Skrydis
                                           trunka 20-30 min.
                                           """)
                           )
                ]

def list_coupon_types():
    return coupon_types;

def get_coupon_type(id):
    for ct in coupon_types:
        if ct.id == id:
            return ct

    raise ValueError("Coupon type %s not found")


class Counter(db.Model):
    cnt = db.IntegerProperty(default=0L, indexed=False)

@db.transactional
def counter_next():
    c = Counter.get_by_key_name('c0')
    if c is None:
        c = Counter(key_name='c0')
    c.cnt += 1
    c.put()
    return c.cnt

class Settings(db.Model):
    """ System settings
    """
    webtopay_project_id = db.StringProperty(required=False, default='')
    webtopay_password = db.StringProperty(required=False, default='')
    debug = db.BooleanProperty(required=True, default=True)
    home_url = db.StringProperty(required=False, default='')

    def is_configured(self):
        return bool(self.webtopay_project_id)

def get_settings(version='main'):
    """ Return dictionary of all application settings.
    """
    entity = Settings.get_or_insert(version)
    # save settings in case schema changed
    entity.put()
    settings = {key: getattr(entity, key)
                for key in Settings.properties().keys()}
    settings['configured'] = entity.is_configured()
    return settings


class Order(db.Model):
    ST_PENDING = 1
    ST_PAID = 2
    ST_CANCELLED = 3
    ST_SPAWNED = 4

    coupon_type = db.StringProperty(required=True)
    quantity = db.IntegerProperty(required=True, default=1)
    price = db.FloatProperty(required=True)
    currency = db.StringProperty(required=True, default='LTL')
    paid_amount = db.FloatProperty()
    paid_currency = db.StringProperty()
    payer_name = db.StringProperty()
    payer_surname = db.StringProperty()
    payer_email = db.EmailProperty()
    payment_provider = db.StringProperty()
    test = db.BooleanProperty(required=True, default=False)
    status = db.IntegerProperty(required=True, default=ST_PENDING,
                                choices=set([ST_PENDING, ST_PAID,
                                             ST_CANCELLED, ST_SPAWNED]))
    create_time = db.DateTimeProperty(required=True)
    payment_time = db.DateTimeProperty()
    notes = db.StringProperty()

    @property
    def order_id(self):
        return self.key().name()

    def is_paid(self):
        return self.status == Order.ST_PAID

    def get_coupon_type(self):
        return get_coupon_type(self.coupon_type)

def order_gen_id():
    """Generate unique order id.
    """
    cnt = counter_next()
    return str(cnt)

def order_get(key_name):
    return Order.get_by_key_name(key_name)

@db.transactional
def order_create(order_id, coupon_type, test=False):
    order = Order(key_name=order_id,
                  coupon_type=coupon_type.id,
                  price=coupon_type.price,
                  currency='LTL',
                  test=test,
                  create_time=datetime.datetime.now(),
                  status=Order.ST_PENDING)
    db.put(order)
    logging.info("Order %s (%s, test=%s) created" % (order_id, coupon_type, test))
    return order

@db.transactional
def order_cancel(order_id):
    """ Cancel order

    Order status is set to ST_CANCELLED.
    """
    order = Order.get_by_key_name(order_id)
    if order.status != Order.ST_PENDING:
        raise ValueError("Cannot cancel non-pending order %s" % order_id)
    order.status = Order.ST_CANCELLED
    db.put(order)
    logging.info("Order %s cancelled" % order.order_id)
    return order

@db.transactional(xg=True)
def order_process(order_id, payer_email,
                  paid_amount, paid_currency,
                  payer_name=None, payer_surname=None, payment_provider=None):
    """ Process order payment.

    Updates order with supplied information and updates status to ST_PAID.
    Creates Coupon object.  Payment information must be validated before
    passing to this method.

    Returns pair: order, coupons
    """
    order = Order.get_by_key_name(order_id)
    if order.status != Order.ST_PENDING:
        raise ValueError("Cannot process non-pending order %s" % order_id)

    order.paid_amount = paid_amount
    order.paid_currency = paid_currency
    order.payer_email = payer_email
    order.payer_name = payer_name
    order.payer_surname = payer_surname
    order.status = Order.ST_PAID
    order.payment_time = datetime.datetime.now()
    db.put(order)
    logging.info("Order %s processed" % order.order_id)

    # create coupon
    assert order.quantity == 1
    coupons = coupon_create(order)

    return order, coupons

def order_find_coupons(order_id):
    orderkey = db.Key.from_path('Order', order_id)
    res = Coupon.all().filter('order =', orderkey)
    return list(res)


def order_count_by_status():
    """Return order statistics by status.

    Pending orders are explicitly excluded.
    """
    counts = defaultdict(int)

    orders = Order.all()
    orders.filter("test =", False)
    orders.filter("status != ", Order.ST_PENDING)
    for order in orders:
        counts[order.status] += 1

    return counts

class Coupon(db.Model):
    ST_ACTIVE = 1
    ST_USED = 2
    order = db.ReferenceProperty(Order)
    status = db.IntegerProperty(required=True, default=ST_ACTIVE,
                                choices=set([ST_ACTIVE, ST_USED]))
    use_time = db.DateTimeProperty()

    @property
    def coupon_id(self):
        return self.key().name()

    @property
    def active(self):
        return self.status == Coupon.ST_ACTIVE

def coupon_get(key_name):
    return Coupon.get_by_key_name(key_name)

def coupon_gen_id():
    """Generate unique order id.
    """
    cnt = counter_next()
    # add some random digits to make order ids less predictable
    seed = ''.join(random.choice(string.digits) for i in range(6))
    year = datetime.datetime.now().strftime('%y')
    return "%s%s%s" % (year, cnt, seed)

def coupon_create(order):
    coupons = []
    for x in range(order.quantity):
        coupon_id = coupon_gen_id()
        coupon = Coupon(order=order, key_name=coupon_id)
        db.put(coupon)
        coupons.append(coupon)
        logging.info("Coupon %s created" % coupon_id)

    return coupons

@db.transactional
def coupon_use(coupon_id):
    c = coupon_get(coupon_id)
    if not c.active:
        raise ValueError("Cannot use non-active coupon %s" % coupon_id)
    c.status = Coupon.ST_USED
    c.use_time = datetime.datetime.now()
    db.put(c)
    logging.info("Coupon %s used" % coupon_id)
    return c


def coupon_list_active():
    return Coupon.all().filter('status =', Coupon.ST_ACTIVE).order('__key__')


def coupon_count_active():
    return coupon_list_active().count()


def coupon_spawn(coupon_type, count, email, notes, test=False):
    """ Create given number of coupons without going through purchase workflow

    """
    logging.info("Spawning %s coupons", count)
    order_id = order_gen_id()

    order = order_create(order_id, coupon_type, test=test)
    order.status = Order.ST_SPAWNED
    order.notes = notes
    order.payer_email = email
    order.quantity = count
    order.payment_time = datetime.datetime.now()
    db.put(order)

    return coupon_create(order)


def coupon_count_by_type():
    counts = defaultdict(int)

    coupons = Coupon.all()
    for coupon in coupons:
        if coupon.order.test:
            continue
        counts[coupon.order.coupon_type] += 1

    return counts
