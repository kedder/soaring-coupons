from typing import Dict, Any, cast
import logging
import io
import re

import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.conf import settings
from django.urls import reverse
from django.template import loader

from coupons import models, webtopay, mailgun

log = logging.getLogger(__name__)


def index(request) -> HttpResponse:
    return HttpResponse("Hello, world. You're at the polls index.")


def order(request: HttpRequest, coupon_type: str) -> HttpResponse:
    ct = get_object_or_404(models.CouponType, pk=coupon_type)
    assert ct.in_stock, "Cannot order this item"
    order = models.Order.single(ct)
    order.save()
    log.info(f"Order {order.id} ({order.coupon_type.id}) created")
    data = _prepare_webtopay_request(order, ct, request)
    url = webtopay.get_redirect_to_payment_url(data)
    return redirect(url)


def _prepare_webtopay_request(
    order: models.Order, ct: models.CouponType, request: HttpRequest
) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    data["projectid"] = settings.COUPONS_WEBTOPAY_PROJECT_ID
    data["sign_password"] = settings.COUPONS_WEBTOPAY_PASSWORD
    data["cancelurl"] = request.build_absolute_uri(reverse("order_cancel"))
    data["accepturl"] = ""  # request.build_absolute_uri(reverse("accept"))
    data["callbackurl"] = request.build_absolute_uri(reverse("order_callback"))
    data["orderid"] = order.id
    data["lang"] = "LIT"
    data["amount"] = order.price * 100
    data["currency"] = order.currency
    data["country"] = "LT"
    data["paytext"] = "%s. Užsakymas nr. [order_nr] svetainėje " "[site_name]" % (
        ct.title
    )
    data["test"] = order.test
    return data


def order_cancel(request: HttpRequest) -> HttpResponse:
    return render(request, "cancel.html", {})


def order_callback(request: HttpRequest) -> HttpResponse:
    params = webtopay.validate_and_parse_data(
        cast(Dict[str, str], request.GET.dict()),
        settings.COUPONS_WEBTOPAY_PROJECT_ID,
        settings.COUPONS_WEBTOPAY_PASSWORD,
    )

    orderid = params["orderid"]
    status = params["status"]
    log.info(f"Executing callback for order {orderid} with status {status}")

    order = get_object_or_404(models.Order, pk=orderid)

    if status == webtopay.STATUS_SUCCESS:
        # Process the order
        paid_amount = int(params["payamount"]) / 100.0
        coupons = order.process(
            paid_amount=paid_amount,
            payer_email=params["p_email"],
            paid_currency=params["paycurrency"],
            payer_name=params.get("name"),
            payer_surname=params.get("surename"),
            payment_provider=params["payment"],
        )

        for coupon in coupons:
            _send_confirmation_email(coupon, request)
    else:
        log.warning("Request unprocessed. params: %s" % params)

    return HttpResponse("OK")


def order_accept(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(models.Order, pk=order_id)
    coupons = order.find_coupons()
    values = {"order": order, "coupons": coupons}
    return render(request, "accept.html", values)


def coupon(request: HttpRequest, coupon_id: str) -> HttpResponse:
    coupon = get_object_or_404(models.Coupon, pk=coupon_id)
    return render(request, "coupon.html", {"coupon": coupon})


def coupon_qr(request: HttpRequest, coupon_id: str) -> HttpResponse:
    coupon = get_object_or_404(models.Coupon, pk=coupon_id)
    url = request.build_absolute_uri(
        reverse("coupon_check", kwargs={"coupon_id": coupon.id})
    )
    qr = qrcode.QRCode(box_size=6, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    imgbuf = io.BytesIO()
    img = qr.make_image()
    img.save(imgbuf)
    return HttpResponse(imgbuf.getvalue(), content_type="image/png")


def coupon_check(request: HttpRequest, coupon_id: str) -> HttpResponse:
    pass


EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def _send_confirmation_email(coupon: models.Coupon, request: HttpRequest) -> None:
    subject = "Kvietimas skrydziui " "Paluknio aerodrome nr. %s" % coupon.id
    coupon_url = request.build_absolute_uri(
        reverse("coupon", kwargs={"coupon_id": coupon.id})
    )
    body = loader.render_to_string(
        "coupon_email.txt", {"coupon": coupon, "url": coupon_url}
    )

    logging.info("Sending confirmation email to %s" % coupon.order.payer_email)
    if settings.DEBUG:
        logging.warning("Not sending email in debug mode")
        return

    assert coupon.order.payer_email is not None
    mailgun.send_mail(
        settings.COUPONS_MAILGUN_DOMAIN,
        settings.COUPONS_MAILGUN_APIKEY,
        sender=settings.COUPONS_EMAIL_SENDER,
        reply_to=settings.COUPONS_EMAIL_REPLYTO,
        bcc=settings.COUPONS_EMAIL_SENDER,
        to=coupon.order.payer_email,
        subject=subject,
        body=body,
    )
