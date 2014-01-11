""" Functions for debugging through Interactive Console

To call one of the functions, defined below, enter into the Interactive
console::

    from soaringcoupons import debug

    debug.function()
"""

from soaringcoupons import model


def create_coupon():
    """Create sample order and process it
    """
    oid = model.order_gen_id()
    ct = model.get_coupon_type('acro')
    model.order_create(oid, ct, test=True)
    model.order_process(oid, 'test@test.com', 300.0, 'LTL')

    print "Coupon %s created" % oid
    print "See http://localhost:8080/coupon/%s" % oid
