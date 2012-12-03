import webapp2

from soaringcoupons import controller
from soaringcoupons import model

settings = model.get_settings()

if not settings['configured']:
    routes = [(r'/', controller.UnconfiguredHandler)]
else:
    routes = controller.get_routes()

app = webapp2.WSGIApplication(routes=routes, debug=settings['debug'],
                              config=settings)
