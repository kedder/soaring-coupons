# -*- coding: utf-8 -*-
import re
import logging
from email.header import Header

import webapp2
import qrcode
from wtforms import Form, validators, SelectField, TextField, IntegerField
from google.appengine.api import mail, memcache

from soaringcoupons import model
from soaringcoupons.template import write_template, render_template
from soaringcoupons import webtopay


def get_routes():
    return [webapp2.Route(r'/', handler=MainHandler, name='home'),
            webapp2.Route(r'/order/<name>', handler=OrderHandler, name='order'),
            webapp2.Route(r'/cancel', handler=OrderCancelHandler,
                          name='wtp_cancel'),
            webapp2.Route(r'/callback', handler=OrderCallbackHandler,
                          name='wtp_callback'),
            webapp2.Route(r'/accept/<id>', handler=OrderAcceptHandler,
                          name='wtp_accept'),
            webapp2.Route(r'/coupon/<id>', handler=CouponHandler,
                          name='coupon'),
            webapp2.Route(r'/qr/<id>', handler=CouponQrHandler, name='qr'),

            webapp2.Route(r'/admin', handler=DashboardHandler,
                          name='dashboard'),
            webapp2.Route(r'/admin/check/<id>', handler=CheckHandler,
                          name='check'),
            webapp2.Route(r'/admin/list', handler=CouponListHandler,
                          name='list_active'),
            webapp2.Route(r'/admin/spawn', handler=CouponSpawnHandler,
                          name='spawn'),
            ]


class UnconfiguredHandler(webapp2.RequestHandler):
    def get(self):
        write_template(self.response, 'unconfigured.html')


class MainHandler(webapp2.RequestHandler):
    def get(self):
        home_url = self.app.config['home_url']
        if home_url:
            webapp2.redirect(home_url, abort=True)
            return

        values = {'coupon_types': model.list_coupon_types()}
        write_template(self.response, 'index.html', values)


EMAIL_RE = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

EMAIL_SENDER = "Vilniaus Aeroklubas <dalia.vainiene@gmail.com>"
EMAIL_REPLYTO = "Vilniaus Aeroklubas <aeroklubas@sklandymas.lt>"


def send_confirmation_email(coupon):
    subject = (u"Kvietimas skrydziui sklandytuvu "
               u"Paluknio aerodrome nr. %s" % coupon.coupon_id)
    coupon_url = webapp2.uri_for('coupon', id=coupon.coupon_id, _full=True)
    body = render_template('coupon_email.txt', {'coupon': coupon,
                                                'url': coupon_url})
    logging.info("Sending confirmation email to %s" % coupon.order.payer_email)
    mail.send_mail(sender=EMAIL_SENDER,
                   reply_to=EMAIL_REPLYTO,
                   to=coupon.order.payer_email,
                   subject=Header(subject, 'utf-8').encode(),
                   body=body)


class OrderHandler(webapp2.RequestHandler):
    def get(self, name):
        ct = model.get_coupon_type(name)
        self.show_form(ct)

    def post(self, name):
        ct = model.get_coupon_type(name)

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

    def prepare_webtopay_request(self, order, ct):
        data = {}
        data['projectid'] = self.app.config['webtopay_project_id']
        data['sign_password'] = self.app.config['webtopay_password']
        data['cancelurl'] = webapp2.uri_for('wtp_cancel', _full=True)
        data['accepturl'] = webapp2.uri_for('wtp_accept', id=order.order_id,
                                            _full=True)
        data['callbackurl'] = webapp2.uri_for('wtp_callback', _full=True)
        data['orderid'] = order.order_id
        data['lang'] = 'LIT'
        data['amount'] = order.price * 100
        data['currency'] = order.currency
        data['country'] = 'LT'
        data['paytext'] = (u'%s. Užsakymas nr. [order_nr] svetainėje '
                           u'[site_name]' % (ct.title))
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
        logging.info("Executing callback for order %s with status %s" %
                     (orderid, status))

        if status == webtopay.STATUS_SUCCESS:
            order, coupons = self.process_order(orderid, params)
            for coupon in coupons:
                send_confirmation_email(coupon)
        else:
            logging.info("Request unprocessed. params: %s" % params)

        self.response.out.write('OK')

    def process_order(self, orderid, params):
        paid_amount = int(params['payamount']) / 100.0
        return model.order_process(orderid, params['p_email'],
                                   paid_amount, params['paycurrency'],
                                   payer_name=params.get('name'),
                                   payer_surname=params.get('surename'),
                                   payment_provider=params['payment'])


class OrderAcceptHandler(webapp2.RequestHandler):
    def get(self, id):
        order = model.order_get(id)
        if order is None:
            webapp2.abort(404)

        coupons = model.order_find_coupons(order.order_id)
        coupon_urls = map(lambda c: webapp2.uri_for('coupon', id=c.coupon_id),
                          coupons)

        values = {'order': order,
                  'coupons': zip(coupons, coupon_urls)}
        write_template(self.response, 'accept.html', values)


class CouponHandler(webapp2.RequestHandler):
    def get(self, id):
        coupon = model.coupon_get(id)
        if coupon is None:
            webapp2.abort(404)

        values = {'coupon': coupon,
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

    def post(self, id):
        model.coupon_use(id)
        msg = "Kvietimas panaudotas"
        webapp2.redirect(webapp2.uri_for('list_active', msg=msg), abort=True)


class CouponListHandler(webapp2.RequestHandler):
    def get(self):
        values = {'coupons': model.coupon_list_active(),
                  'coupon_count': model.coupon_count_active(),
                  'check_url': lambda id: webapp2.uri_for('check', id=id)}
        write_template(self.response, 'coupon_list.html', values)


class CouponSpawnForm(Form):
    coupon_type = SelectField(u'Skrydžio tipas',
                              [validators.InputRequired()])
    email = TextField(u'El. pašto adresas',
                      [validators.InputRequired(),
                       validators.Regexp(EMAIL_RE,
                                         message=u'Invalid e-mail address.')])
    count = IntegerField(u'Kvietimų kiekis',
                         [validators.InputRequired(),
                          validators.NumberRange(min=1, max=100)])
    notes = TextField(u'Pastabos',
                      [validators.InputRequired()])

    def __init__(self, *args, **kwargs):
        super(CouponSpawnForm, self).__init__(*args, **kwargs)
        ctypes = [(t.id, t.title) for t in model.list_coupon_types()]
        ctypes.insert(0, ('', ''))  # empty choice at the front
        self.coupon_type.choices = ctypes


class CouponSpawnHandler(webapp2.RequestHandler):
    def get(self):
        form = CouponSpawnForm()
        values = {'form': form}
        write_template(self.response, 'coupon_spawn.html', values)

    def post(self):
        form = CouponSpawnForm(self.request.params)
        if form.validate():
            self.generate(form.data)
            webapp2.redirect(webapp2.uri_for('spawn',
                                             msg='Kvietimai sugeneruoti'),
                             abort=True)
            return

        else:
            values = {'form': form}
            write_template(self.response, 'coupon_spawn.html', values)

    def generate(self, data):
        ct = model.get_coupon_type(data['coupon_type'])
        coupons = model.coupon_spawn(ct, data['count'],
                                     data['email'], data['notes'],
                                     test=self.app.config['debug'])

        for c in coupons:
            send_confirmation_email(c)


class DashboardHandler(webapp2.RequestHandler):
    def get(self):
        values = memcache.get('stats')
        if not values:
            byorderstatus = model.order_count_by_status()
            bytype = model.coupon_count_by_type()
            bycouponstatus = model.coupon_count_by_status()

            values = {'orders_by_status': byorderstatus,
                      'coupons_by_type': bytype,
                      'coupons_by_status': bycouponstatus}
            logging.info("Uncached: %s" % values)
            memcache.add('stats', values, 60 * 60 * 24)

        write_template(self.response, "dashboard.html", values)
