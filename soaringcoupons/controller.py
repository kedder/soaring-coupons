# -*- coding: utf-8 -*-
from __future__ import absolute_import

import re
import webapp2

from soaringcoupons.model import list_coupon_types, get_coupon_type
from soaringcoupons.template import write_template

class MainHandler(webapp2.RequestHandler):
    def get(self):
        values = {'coupon_types': list_coupon_types()}
        write_template(self.response, 'index.html', values)


ERR_MISSING = u'Laukas yra privalomas'
ERR_INVALID_EMAIL = u'Nekorektiškas el. pašto adresas'

EMAIL_RE = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

class OrderHandler(webapp2.RequestHandler):
    def get(self, id):
        ct = get_coupon_type(id)
        self.show_form(ct)

    def post(self, id):
        ct = get_coupon_type(id)
        errors = self.validate()
        if errors:
            self.show_form(ct, errors)
            return

        self.response.out.write("Posted")

    def show_form(self, ct, errors={}):
        values = {'request': self.request.params,
                  'coupon_type': ct,
                  'errors': errors}
        write_template(self.response, 'order.html', values)

    def validate(self):
        """ Validate form input
        """
        errors = {}

        # Validate required fields
        for field in ['name', 'surname', 'email']:
            if not self.request.get(field):
                errors[field] = ERR_MISSING

        # validate email
        if 'email' not in errors:
            if not EMAIL_RE.match(self.request.get('email')):
                errors['email'] = ERR_INVALID_EMAIL
        return errors
