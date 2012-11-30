from __future__ import absolute_import

from google.appengine.ext import db

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


class Settings(db.Model):
    webtopay_project_id = db.StringProperty(required=False, default='')
    webtopay_password = db.StringProperty(required=False, default='')
    debug = db.BooleanProperty(required=True, default=True)

    def is_configured(self):
        return bool(self.webtopay_project_id)

def get_settings():
    """ Return dictionary of all application settings.
    """
    entity = Settings.get_or_insert('main')
    # save settings in case schema changed
    entity.put()
    settings = {key: getattr(entity, key)
                for key in Settings.properties().keys()}
    settings['configured'] = entity.is_configured()
    return settings
