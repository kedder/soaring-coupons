import hashlib
import urllib
import base64

# WebToPay Library version.
VERSION = '1.6'

# Server URL where all requests should go.
PAY_URL = 'https://www.mokejimai.lt/pay/'

# Server URL where we can get XML with payment method data.
XML_URL = 'https://www.mokejimai.lt/new/api/paymentMethods/'

class WebToPayException(Exception):
    pass

def build_request(data):
    """ Builds request data array.

    This method checks all given data and generates correct request data
    array or raises WebToPayException on failure.

    Possible keys:
        https://www.mokejimai.lt/makro_specifikacija.html

    data - Information about current payment request

    throws WebToPayException on data validation error

    ported from WebToPay->buildRequest
    """
    # Validate data
    if 'sign_password' not in data or 'projectid' not in data:
        raise WebToPayException('sign_password or projectid is not provided')

    projectid = data.pop('projectid')
    password = data.pop('sign_password')

    qs = _prepare_query_string(data, projectid)
    qs64 = _safe_base64_encode(qs)
    return {'data': qs64,
            'sign': hashlib.md5(qs64 + password).hexdigest()}

def get_redirect_to_payment_url(data):
    """ Builds request and returns url to payment page with generated request
    data

    Possible array keys are described here:
        https://www.mokejimai.lt/makro_specifikacija.html

    data - Information about current payment request.

    Raises WebToPayException on data validation error

    ported from WebToPay->redirectToPayment()
    """

def validate_and_parse_data(query, project_id, password):
    """ Parses request (query) data and validates its signature.

    query - usually GET data
    Raises WebToPayException

    """


def _prepare_query_string(data, projectid):
    params = {'projectid': projectid,
              'version': VERSION}
    params.update(data)
    return urllib.urlencode(params)

def _safe_base64_encode(s):
    """Encodes string to url-safe-base64

    Url-safe-base64 is same as base64, but + is replaced to - and / to _
    """
    s64 = base64.b64encode(s)
    return s64.replace('+', '-').replace('/', '_')
