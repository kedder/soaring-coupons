import os
import webapp2

from soaringcoupons import controller
from soaringcoupons import model


def make_app():
    cvid = os.environ['CURRENT_VERSION_ID']
    version, ts = cvid.split('.') if '.' in cvid else ('test', '0')
    settings = model.get_settings(version)
    if not settings['configured']:
        routes = [webapp2.Route(r'/',
                                controller.UnconfiguredHandler, name='home')]
    else:
        routes = controller.get_routes()

    return webapp2.WSGIApplication(routes=routes, debug=settings['debug'],
                                   config=settings)

app = make_app()
