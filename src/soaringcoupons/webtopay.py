import hashlib
import urllib
import urlparse
import base64

# WebToPay Library version.
VERSION = '1.6'

# Server URL where all requests should go.
PAY_URL = 'https://www.mokejimai.lt/pay/'

# Server URL where we can get XML with payment method data.
XML_URL = 'https://www.mokejimai.lt/new/api/paymentMethods/'

STATUS_NOT_PAID = '0'
STATUS_SUCCESS = '1'
STATUS_DELAYED = '2'
STATUS_EXTRA = '3'


class WebToPayException(Exception):
    # Missing field.
    E_MISSING = 1

    # Invalid field value.
    E_INVALID = 2

    # Max length exceeded.
    E_MAXLEN = 3

    # Regexp for field value doesn't match.
    E_REGEXP = 4

    # Missing or invalid user given parameters.
    E_USER_PARAMS = 5

    # Logging errors
    E_LOG = 6

    # SMS answer errors
    E_SMS_ANSWER = 7

    # Macro answer errors
    E_STATUS = 8

    # Library errors - if this happens, bug-report should be sent also you can
    # check for newer version
    E_LIBRARY = 9

    # Errors in remote service - it returns some invalid data
    E_SERVICE = 10

    # Deprecated usage errors
    E_DEPRECATED_USAGE = 11

    def __init__(self, message, code=0):
        super(WebToPayException, self).__init__(message)
        self.code = code
        self.field = None


class WebToPayException_Callback(WebToPayException):
    pass


class WebToPayException_Validation(WebToPayException):
    def __init__(self, message, code=0, field=None):
        super(WebToPayException_Validation, self).__init(message, code)
        self.field = field


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
            'sign': _sign(qs64, password)}


def get_redirect_to_payment_url(data):
    """ Builds request and returns url to payment page with generated request
    data

    Possible array keys are described here:
        https://www.mokejimai.lt/makro_specifikacija.html

    data - Information about current payment request.

    Raises WebToPayException on data validation error

    ported from WebToPay->redirectToPayment()
    """
    rq = build_request(data)
    return '%s?%s' % (PAY_URL, urllib.urlencode(rq))


def validate_and_parse_data(query, project_id, password):
    """ Parses request (query) data and validates its signature.

    query - usually GET data.

    Raises WebToPayException.
    """
    if 'data' not in query:
        raise WebToPayException('"data" parameter not found')

    data64 = query['data']
    ss1 = query['ss1']
    # ss2 = query['ss2']
    if not _is_valid_ss1(ss1, data64, password):
        raise WebToPayException('Signature ss1 is not valid')

    request = _parse_data(data64)

    # validate request dict
    if 'projectid' not in request:
        raise WebToPayException_Callback('"projectid" not provided in callback',
                                         WebToPayException.E_INVALID)
    if request['projectid'] != project_id:
        raise WebToPayException_Callback(
            'Bad project id: %s, should be: %s' %
            (request['projectid'], project_id), WebToPayException.E_INVALID)

    if 'type' not in request or request['type'] not in ('micro', 'macro'):
        micro = 'to' in request and 'from' in request and 'sms' in request
        request['type'] = 'micro' if micro else 'macro'

    return request


def _sign(data, password):
    return hashlib.md5(data + password).hexdigest()


def _is_valid_ss1(ss1, data, password):
    sig = hashlib.md5(data + password).hexdigest()
    return ss1 == sig


def _parse_data(data):
    s = _safe_base64_decode(data)
    return {k: unicode(v, 'utf-8', errors='replace')
            for k, v in urlparse.parse_qsl(s)}


def _prepare_query_string(data, projectid):
    params = {k: unicode(v).encode('utf-8') for k, v in data.items()}
    params['projectid'] = projectid
    params['version'] = VERSION
    return urllib.urlencode(params)


def _safe_base64_encode(s):
    """Encodes string to url-safe-base64

    Url-safe-base64 is same as base64, but + is replaced to - and / to _
    """
    s64 = base64.b64encode(s)
    return s64.replace('+', '-').replace('/', '_')


def _safe_base64_decode(s64):
    """Decodes url-safe-base64 encoded string

    Url-safe-base64 is same as base64, but + is replaced to - and / to _
    """
    s = s64.replace('-', '+').replace('_', '/')
    return base64.b64decode(s)
