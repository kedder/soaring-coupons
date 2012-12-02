from __future__ import absolute_import

import webapp2

from soaringcoupons import controller
from soaringcoupons import model

routes = [webapp2.Route(r'/',
                        handler=controller.MainHandler,
                        name='home'),
          webapp2.Route(r'/order/<name>',
                        handler=controller.OrderHandler,
                        name='order'),
          webapp2.Route(r'/accept',
                        handler=controller.OrderAcceptHandler,
                        name='wtp_accept'),
          webapp2.Route(r'/cancel',
                        handler=controller.OrderCancelHandler,
                        name='wtp_cancel'),
          webapp2.Route(r'/callback',
                        handler=controller.OrderCallbackHandler,
                        name='wtp_callback'),
          ]

settings = model.get_settings()

if not settings['configured']:
    routes = [(r'/', controller.UnconfiguredHandler)]

app = webapp2.WSGIApplication(routes=routes, debug=settings['debug'],
                              config=settings)
