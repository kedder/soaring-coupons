# -*- coding: utf-8 -*-
import re
import logging
from email.header import Header

import webapp2
import qrcode
from google.appengine.api import mail

from soaringcoupons import model
from soaringcoupons.template import write_template, render_template
from soaringcoupons import webtopay

def get_routes():
    return [webapp2.Route(r'/', handler=MainHandler, name='home'),
            webapp2.Route(r'/order/<name>', handler=OrderHandler, name='order'),
            webapp2.Route(r'/cancel', handler=OrderCancelHandler, name='wtp_cancel'),
            webapp2.Route(r'/callback', handler=OrderCallbackHandler, name='wtp_callback'),
            webapp2.Route(r'/accept/<id>', handler=OrderAcceptHandler, name='wtp_accept'),
            webapp2.Route(r'/coupon/<id>', handler=CouponHandler, name='coupon'),
            webapp2.Route(r'/qr/<id>', handler=CouponQrHandler, name='qr'),
            webapp2.Route(r'/check/<id>', handler=CheckHandler, name='check'),
            webapp2.Route(r'/admin/list', handler=CouponListHandler, name='check'),
            ]

class UnconfiguredHandler(webapp2.RequestHandler):
    def get(self):
        write_template(self.response, 'unconfigured.html')

class MainHandler(webapp2.RequestHandler):
    def get(self):
        values = {'coupon_types': model.list_coupon_types()}
        write_template(self.response, 'index.html', values)


ERR_MISSING = u'Laukas yra privalomas'
ERR_INVALID_EMAIL = u'Nekorektiškas el. pašto adresas'

EMAIL_RE = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

EMAIL_SENDER = "Vilniaus Aeroklubas <aeroklubas@sklandymas.lt>"

class OrderHandler(webapp2.RequestHandler):
    def get(self, name):
        ct = model.get_coupon_type(name)
        self.show_form(ct)

    def post(self, name):
        ct = model.get_coupon_type(name)
        #errors = self.validate()
        #if errors:
        #    self.show_form(ct, errors)
        #    return

        order_id = model.order_gen_id()
        order = model.order_create(order_id, ct, test=self.app.config['debug'])

        data = self.prepare_webtopay_request(order, ct)
        logging.info('Starting payment transaction for %s' % data)
        url = webtopay.get_redirect_to_payment_url(data)
        webapp2.redirect(url, abort=True)

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

    def prepare_webtopay_request(self, order, ct):
        data = {}
        data['projectid'] = self.app.config['webtopay_project_id']
        data['sign_password'] = self.app.config['webtopay_password']
        data['cancelurl'] = webapp2.uri_for('wtp_cancel', _full=True)
        data['accepturl'] = webapp2.uri_for('coupon', id=order.order_id, _full=True)
        data['callbackurl'] = webapp2.uri_for('wtp_callback', _full=True)
        data['orderid'] = order.order_id
        data['lang'] = 'LIT'
        data['amount'] = order.price * 100
        data['currency'] = 'LTL'
        data['country'] = 'LT'
        data['paytext'] = (u'%s. Užsakymas nr. [order_nr] svetainėje [site_name]' \
                           % (ct.description))
        data['test'] = order.test

        return data

class OrderCancelHandler(webapp2.RequestHandler):
    def get(self):
        write_template(self.response, 'cancel.html')

class OrderCallbackHandler(webapp2.RequestHandler):
    def get(self):
        config = self.app.config
        params = webtopay.validate_and_parse_data(self.request.params,
                                                  config['webtopay_project_id'],
                                                  config['webtopay_password'])

        orderid = params['orderid']
        status = params['status']
        if status == webtopay.STATUS_SUCCESS:
            order, coupon = self.process_order(orderid, params)
            self.send_confirmation_email(coupon)

        self.response.out.write('OK')
        logging.info("Callback for order %s executed with status %s" % \
                     (orderid, status))

    def process_order(self, orderid, params):
        paid_amount = int(params['payamount']) / 100.0
        return model.order_process(orderid, params['p_email'],
                                   paid_amount, params['paycurrency'],
                                   payer_name=params['name'],
                                   payer_surname=params['surename'],
                                   payment_provider=params['payment'])

    def send_confirmation_email(self, coupon):
        subject = u"Jūsų kvietimas pagal užsakymą %s" % coupon.order.order_id
        coupon_url = webapp2.uri_for('coupon', id=coupon.coupon_id, _full=True)
        body = render_template('coupon_email.txt', {'coupon': coupon,
                                                    'url': coupon_url})
        mail.send_mail(sender=EMAIL_SENDER,
                       to=coupon.order.payer_email,
                       subject=Header(subject, 'utf-8').encode(),
                       body=body)

class OrderAcceptHandler(webapp2.RequestHandler):
    def get(self, id):
        order = model.order_get(id)
        if order is None:
            webapp2.abort(404)

        values = {'order': order,
                  'coupon_url': webapp2.uri_for('coupon', id=order.order_id)}
        write_template(self.response, 'accept.html', values)

class CouponHandler(webapp2.RequestHandler):
    def get(self, id):
        coupon = model.coupon_get(id)
        if coupon is None:
            webapp2.abort(404)

        values = {'coupon': coupon,
                  'coupon_type': coupon.order.get_coupon_type(),
                  'qr': webapp2.uri_for('qr', id=id)
                  }

        write_template(self.response, 'coupon.html', values)

class CouponQrHandler(webapp2.RequestHandler):
    def get(self, id):
        url = webapp2.uri_for('check', id=id, _full=True)
        qr = qrcode.QRCode(box_size=6,
                           border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()

        self.response.headers.add("Content-Type", "image/png")
        img.save(self.response.out)

class CheckHandler(webapp2.RequestHandler):
    def get(self, id):
        coupon = model.coupon_get(id)
        if coupon is None:
            webapp2.abort(404)

        values = {'coupon': coupon}
        write_template(self.response, 'check.html', values)

class CouponListHandler(webapp2.RequestHandler):
    def get(self):
        values = {'coupons': model.coupon_list_active(),
                  'coupon_count': model.coupon_count_active()}
        write_template(self.response, 'coupon_list.html', values)
