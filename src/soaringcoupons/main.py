import os
import webapp2

from soaringcoupons import controller
from soaringcoupons import model

version, ts = os.environ['CURRENT_VERSION_ID'].split('.')
settings = model.get_settings(version)
if not settings['configured']:
    routes = [webapp2.Route(r'/', controller.UnconfiguredHandler, name='home')]
else:
    routes = controller.get_routes()

app = webapp2.WSGIApplication(routes=routes, debug=settings['debug'],
                              config=settings)
