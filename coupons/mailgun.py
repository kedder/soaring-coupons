import requests


def send_mail(
    domain: str,
    apikey: str,
    sender: str,
    to: str,
    subject: str,
    body: str,
    reply_to: str = None,
    bcc: str = None,
) -> None:
    url = f"https://api.mailgun.net/v3/{domain}/messages"

    response = requests.post(
        url,
        auth=("api", apikey),
        data={"from": sender, "to": to, "subject": subject, "text": body, "bcc": bcc},
    )

    if response.status_code != 200:
        raise RuntimeError(f"Mailgun API error: {response.status_code} {response.text}")
