from __future__ import absolute_import

import webapp2

from soaringcoupons import controller
from soaringcoupons import model

routes = [(r'/', controller.MainHandler),
          (r'/order/(.+)', controller.OrderHandler)]

settings = model.get_settings()

if not settings['configured']:
    routes = [(r'/', controller.UnconfiguredHandler)]

app = webapp2.WSGIApplication(routes=routes, debug=settings['debug'],
                              config=settings)
