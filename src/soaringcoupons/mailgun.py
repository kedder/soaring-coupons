import httplib2
from urllib import urlencode


def send_mail(domain, apikey,
              sender, to, subject, body, reply_to=None, bcc=None):

    http = httplib2.Http()
    http.add_credentials('api', apikey)

    url = 'https://api.mailgun.net/v3/{}/messages'.format(domain)
    data = {
        'from': sender,
        'to': to,
        'bcc': bcc,
        'subject': subject.encode('utf-8'),
        'text': body.encode('utf-8')
    }

    resp, content = http.request(url, 'POST', urlencode(data))

    if resp.status != 200:
        raise RuntimeError(
            'Mailgun API error: {} {}'.format(resp.status, content))
