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
        return ct.description
    except ValueError:
        return '?'

