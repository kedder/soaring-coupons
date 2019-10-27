from typing import Dict, Any, cast, List, Tuple
import logging
from datetime import date
import io
import re

import qrcode
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.conf import settings
from django.urls import reverse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from coupons import models, webtopay, mailgun

log = logging.getLogger(__name__)


def index(request) -> HttpResponse:
    log.error("Error logged")
    return HttpResponse("Hello, world. You're at the polls index.")


def order(request: HttpRequest, coupon_type: str) -> HttpResponse:
    ct = get_object_or_404(models.CouponType, pk=coupon_type)
    assert ct.in_stock, "Cannot order this item"
    order = models.Order.from_type(ct)
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
    data["accepturl"] = request.build_absolute_uri(
        reverse("order_accept", kwargs={"order_id": order.id})
    )
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


@login_required
def coupon_check(request: HttpRequest, coupon_id: str) -> HttpResponse:
    coupon = get_object_or_404(models.Coupon, pk=coupon_id)
    return render(request, "coupon_check.html", {"coupon": coupon})


@login_required
def coupon_actions(request: HttpRequest, coupon_id: str) -> HttpResponse:
    coupon = get_object_or_404(models.Coupon, pk=coupon_id)
    if "use" in request.POST:
        coupon.use()
        messages.info(request, "Kvietimas panaudotas")
    elif "resend" in request.POST:
        _send_confirmation_email(coupon, request)
        messages.info(request, "Kvietimo laiškas išsiųstas")
    else:
        raise ValueError("Unknown action")
    return redirect(reverse("coupon_check", kwargs={"coupon_id": coupon.id}))


@login_required
def coupon_list(request: HttpRequest) -> HttpResponse:
    years = [v["year"] for v in models.Coupon.objects.values("year").distinct()]

    curyear = int(request.GET.get("year", years[0]))
    coupons = models.Coupon.objects.filter(year=curyear, status=models.Coupon.ST_ACTIVE)

    return render(
        request,
        "coupon_list.html",
        {
            "object_list": coupons,
            "object_count": len(coupons),
            "years": years,
            "requested_year": curyear,
        },
    )


@login_required
def coupon_spawn(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        spawnform = CouponSpawnForm()
        return render(request, "coupon_spawn.html", {"form": spawnform})
    else:
        spawnform = CouponSpawnForm(request.POST)
        if not spawnform.is_valid():
            return render(request, "coupon_spawn.html", {"form": spawnform})

        data = spawnform.cleaned_data
        ct = models.CouponType.objects.get(pk=data["coupon_type"])
        coupons = models.Coupon.spawn(
            ct,
            count=data["count"],
            email=data["email"],
            notes=data["notes"],
            expires=data["expires"],
        )

        for c in coupons:
            _send_confirmation_email(c, request)

        messages.info(request, "Kvietimai sugeneruoti")
        return redirect(reverse("coupon_spawn"))


EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class CouponSpawnForm(forms.Form):
    coupon_type = forms.ChoiceField(
        label="Skrydžio tipas", choices=lambda: CouponSpawnForm.coupon_types()
    )
    email = forms.EmailField(label="El. pašto adresas")
    count = forms.IntegerField(label="Kvietimų kiekis")
    notes = forms.CharField(
        label="Pastabos",
        max_length=1024,
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    expires = forms.TypedChoiceField(
        label="Galioja iki",
        choices=lambda: CouponSpawnForm.expire_choices(),
        coerce=lambda v: CouponSpawnForm.to_date(v),
    )

    @staticmethod
    def coupon_types() -> List[Tuple[str, str]]:
        ctypes = models.CouponType.objects.all()
        return [(ctype.id, ctype.title) for ctype in ctypes]

    @staticmethod
    def expire_choices() -> List[Tuple[str, str]]:
        today = date.today()
        expirations = models.Coupon.get_valid_expirations(today, 7)
        return [(d.isoformat(), d.isoformat()) for d in expirations]

    @staticmethod
    def to_date(v: str) -> date:
        return date.fromisoformat(v)


def _send_confirmation_email(coupon: models.Coupon, request: HttpRequest) -> None:
    subject = "Kvietimas skrydziui " "Paluknio aerodrome nr. %s" % coupon.id
    coupon_url = request.build_absolute_uri(
        reverse("coupon", kwargs={"coupon_id": coupon.id})
    )
    body = loader.render_to_string(
        "coupon_email.txt", {"coupon": coupon, "url": coupon_url}
    )

    log.info("Sending confirmation email to %s" % coupon.order.payer_email)
    if settings.DEBUG:
        log.warning("Not sending email in debug mode")
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
