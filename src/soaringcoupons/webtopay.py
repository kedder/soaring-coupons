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
    pass

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
