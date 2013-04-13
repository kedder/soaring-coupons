# -*- coding: utf-8 -*-
import jinja2

from soaringcoupons import model

def filter_error(value):
    if not value:
        return ''
    return jinja2.Markup("<span class='error'>%s</span>" % value)

def format_datetime(value):
    if value is None:
        return ''

    return value.strftime('%Y-%m-%d %H:%M')

def format_date(value):
    if value is None:
        return ''
    return value.strftime('%Y-%m-%d')

def format_yesno(value):
    return [u'Ne', u'Taip'][bool(value)]

def format_coupon_type(value):
    try:
        ct = model.get_coupon_type(value)
        return ct.title
    except ValueError:
        return '?'


def format_order_status(value):
    statusmap = {model.Order.ST_PENDING: u"Laukia apmokėjimo",
                 model.Order.ST_PAID: u"Apmokėtas",
                 model.Order.ST_CANCELLED: u"Atšauktas",
                 model.Order.ST_SPAWNED: u"Sugeneruotas",
                 }
    return statusmap[value]


