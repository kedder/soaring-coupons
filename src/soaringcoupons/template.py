# -*- coding: utf-8 -*-
import os

import jinja2
import webapp2
from google.appengine.api import users

from soaringcoupons import formatters


def make_globals():
    user = users.get_current_user()
    home = webapp2.uri_for('home')
    version = os.environ['CURRENT_VERSION_ID']
    if '.' in version:
        majorversion, minorversion = version.split('.')
    else:
        majorversion, minorversion = version, ''

    values = {'user': {'logged': user is not None,
                       'admin': users.is_current_user_admin(),
                       'nickname': user.nickname() if user else None,
                       'logout_url': users.create_logout_url(home)
                       },
              'request': webapp2.get_request().params,
              'uri_for': webapp2.uri_for,
              'version': version,
              'majorversion': majorversion,
              }

    return values


def render_template(name, values={}):
    ns = make_globals()
    ns.update(values)
    tpl = jinja_environment.get_template(name)
    return tpl.render(ns)


def write_template(response, name, values={}):
    response.out.write(render_template(name, values))

FILTERS = {'error': formatters.filter_error,
           'datetime': formatters.format_datetime,
           'date': formatters.format_date,
           'yesno': formatters.format_yesno,
           'coupon_type': formatters.format_coupon_type,
           'coupon_status': formatters.format_coupon_status,
           'order_status': formatters.format_order_status,
           }

loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),
                                              'templates'))
jinja_environment = jinja2.Environment(autoescape=True,
                                       undefined=jinja2.StrictUndefined,
                                       loader=loader)
jinja_environment.filters.update(FILTERS)
