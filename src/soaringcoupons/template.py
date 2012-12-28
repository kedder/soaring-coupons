# -*- coding: utf-8 -*-
import os

import jinja2
import webapp2
from google.appengine.api import users

from soaringcoupons import formatters

def make_globals():
    user = users.get_current_user()
    home = webapp2.uri_for('home')

    values = {'user': {'logged': user is not None,
                       'admin': users.is_current_user_admin(),
                       'nickname': user.nickname() if user else None,
                       'logout_url': users.create_logout_url(home)
                       }
              }

    return values

def render_template(name, values={}):
    g = make_globals()
    return jinja_environment.get_template(name, globals=g).render(values)

def write_template(response, name, values={}):
    response.out.write(render_template(name, values))

FILTERS = {'error': formatters.filter_error,
           'datetime': formatters.format_datetime,
           'date': formatters.format_date,
           'yesno': formatters.format_yesno,
           'coupon_type': formatters.format_coupon_type,
           }

loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),
                                              'templates'))
jinja_environment = jinja2.Environment(autoescape=True,
                                       undefined=jinja2.StrictUndefined,
                                       loader=loader)
jinja_environment.filters.update(FILTERS)
