from __future__ import absolute_import

import webapp2

from soaringcoupons import controller

routes = [(r'/', controller.MainHandler),
          (r'/order/(.+)', controller.OrderHandler)]

app = webapp2.WSGIApplication(routes=routes, debug=True)
