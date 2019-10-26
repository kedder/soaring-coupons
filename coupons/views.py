from typing import Dict, Any
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse

from coupons import models, webtopay

log = logging.getLogger(__name__)


def index(request) -> HttpResponse:
    return HttpResponse("Hello, world. You're at the polls index.")


def order(request, coupon_type: str) -> HttpResponse:
    ct = get_object_or_404(models.CouponType, pk=coupon_type)
    assert ct.in_stock, "Cannot order this item"
    order = models.Order.single(ct)
    order.save()
    log.info(f"Order {order.id} ({order.coupon_type.id}) created")
    data = _prepare_webtopay_request(order, ct)
    url = webtopay.get_redirect_to_payment_url(data)
    return redirect(url)


def _prepare_webtopay_request(
    order: models.Order, ct: models.CouponType
) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    data["projectid"] = ""  # self.app.config['webtopay_project_id']
    data["sign_password"] = ""  # self.app.config['webtopay_password']
    data["cancelurl"] = "urlcancel"  # webapp2.uri_for('wtp_cancel', _full=True)
    data["accepturl"] = "urlaccept"  # webapp2.uri_for('wtp_accept', id=order.order_id,
    #    _full=True)
    data["callbackurl"] = "urlcallack"  # webapp2.uri_for('wtp_callback', _full=True)
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


def cancel(request) -> HttpResponse:
    return render(request, 'cancel.html', {})
