from __future__ import absolute_import

class CouponType(object):
    id = None
    price = None
    description = None

    def __init__(self, id, price, description=None):
        self.id = id
        self.price = price
        self.description = description


coupon_types = [CouponType('training', 150.0, 'Mokomasis skrydis'),
                CouponType('acro', 300.0, 'Akrobatinis skrydis')
                ]

def list_coupon_types():
    return coupon_types;

def get_coupon_type(id):
    for ct in coupon_types:
        if ct.id == id:
            return ct

    raise ValueError("Coupon type %s not found")
