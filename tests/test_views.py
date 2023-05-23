import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest import mock

import pytest
from anymail.exceptions import AnymailRequestsAPIError
from coupons import models, webtopay
from django.core import mail


@pytest.fixture
def sample_coupon_type(db):
    ct = models.CouponType(
        id="sample",
        price=12.3,
        title="Test Flight",
        welcome_text="",
        validity_cond_text="",
        deafult_expiration_date=date.today(),
        print_template="flight",
    )
    ct.save()
    return ct


def test_index(client) -> None:
    # WHEN
    response = client.get("/")
    # THEN
    assert response.status_code == 302


def test_robots_txt(client) -> None:
    # WHEN
    response = client.get("/robots.txt")
    # THEN
    assert response.status_code == 200
    assert response.content == b"User-Agent: *\nDisallow: /\n"


def test_about(client, db) -> None:
    # WHEN
    response = client.get("/about")
    # THEN
    assert response.status_code == 200
    assert "Soaring Coupons" in response.content.decode("utf-8")


def test_cancel(client, db) -> None:
    # WHEN
    response = client.get("/cancel")
    # THEN
    assert response.status_code == 200
    assert "Užsakymas atšauktas" in response.content.decode("utf-8")


def test_order(client, sample_coupon_type) -> None:
    # WHEN
    response = client.get(f"/order/{sample_coupon_type.id}")

    # THEN
    assert response.status_code == 302
    assert response.has_header("Location")

    # Order was created
    orders = models.Order.objects.all()

    assert orders.count() == 1

    order = orders[0]
    assert order.coupon_type == sample_coupon_type
    assert not order.paid
    assert order.status == models.Order.ST_PENDING


def test_order_with_discount(client, sample_coupon_type) -> None:
    # GIVEN
    d1 = models.ScheduledDiscount(
        date_from=datetime(2020, 1, 1, 20, 14, tzinfo=timezone.utc),
        date_to=datetime(2020, 1, 10, 22, 12, tzinfo=timezone.utc),
        discount=15,
        comment="Broad",
    )
    d1.save()

    # WHEN
    with mock.patch("coupons.views.datetime") as dt_mock:
        dt_mock.now.return_value = datetime(2020, 1, 4, 0, 0, tzinfo=timezone.utc)
        response = client.get(f"/order/{sample_coupon_type.id}")

    # THEN
    assert response.status_code == 302
    assert response.has_header("Location")

    # Order was created
    orders = models.Order.objects.all()

    assert orders.count() == 1

    order = orders[0]
    assert order.coupon_type == sample_coupon_type
    assert not order.paid
    assert order.status == models.Order.ST_PENDING
    assert order.price == Decimal("10.46")
    assert order.discount == Decimal("1.84")


def test_order_callback_success(mailoutbox, client, sample_coupon_type) -> None:
    # GIVEN
    order = models.Order.from_type(sample_coupon_type)
    order.save()

    # Prepare request as webtopay would
    req = {
        "orderid": order.id,
        "payamount": "20000",
        "paycurrency": "LTL",
        "p_email": "test@test.com",
        "status": "1",
        "name": "Bill",
        "surename": "Gates",
        "payment": "test",
    }

    data = webtopay._safe_base64_encode(webtopay._prepare_query_string(req, "test"))
    signature = webtopay._sign(data, b"pass")

    params = {"data": data, "ss1": signature}
    with mock.patch("coupons.models.Coupon.gen_unique_id") as m:
        m.return_value = "1001"
        resp = client.get("/callback", params)

    assert resp.content == b"OK"

    # Check order status
    order = models.Order.objects.get(id=order.id)
    assert order.paid

    # Check coupon status
    coupons = order.find_coupons()
    assert len(coupons) == 1
    coupon = coupons[0]
    assert coupon.active

    # Make sure email was sent
    assert len(mail.outbox) == 1

    # Make sure email contains correct link to coupon
    msg = mail.outbox[0]
    msg_contents = str(msg.body)
    assert re.findall(r"http://.*/coupon/1001", msg_contents)


def test_order_callback_notif_fail(mailoutbox, client, sample_coupon_type) -> None:
    # GIVEN
    order = models.Order.from_type(sample_coupon_type)
    order.save()

    # Prepare request as webtopay would
    req = {
        "orderid": order.id,
        "payamount": "20000",
        "paycurrency": "LTL",
        "p_email": "test@test.com",
        "status": "1",
        "name": "Bill",
        "surename": "Gates",
        "payment": "test",
    }

    data = webtopay._safe_base64_encode(webtopay._prepare_query_string(req, "test"))
    signature = webtopay._sign(data, b"pass")

    params = {"data": data, "ss1": signature}
    with mock.patch("coupons.models.Coupon.gen_unique_id") as m, mock.patch(
        "django.core.mail.EmailMessage.send"
    ) as s:
        m.return_value = "1001"
        s.side_effect = AnymailRequestsAPIError()
        resp = client.get("/callback", params)

    assert resp.content == b"OK"


def test_order_accept(sample_coupon_type, client):
    order = models.Order.from_type(sample_coupon_type)
    order.save()

    with mock.patch("coupons.models.Coupon.gen_unique_id") as m:
        m.return_value = "1001"
        order.process(
            payer_email="test@test.com", paid_amount=200.0, paid_currency="LTL"
        )

    # load "accept" url
    resp = client.get(f"/accept/{order.id}")
    assert b'<a href="/coupon/1001"' in resp.content


def test_coupon_spawn(mailoutbox, sample_coupon_type, admin_client) -> None:
    resp = admin_client.get("/admin/spawn")
    assert resp.status_code == 200

    # submit with empty fields
    resp = admin_client.post("/admin/spawn", {})
    assert resp.status_code == 200
    assert b"This field is required." in resp.content

    # email validation works
    resp = admin_client.post("/admin/spawn", {"email": "hello@wiorld@gmail.com"})
    assert resp.status_code == 200
    assert b"Enter a valid email address." in resp.content

    # Find all exporation date choices
    expirations = re.findall(
        r'value="(\d\d\d\d-\d\d-\d\d)"', resp.content.decode("utf-8")
    )

    # submit correct fields
    data = {
        "coupon_type": sample_coupon_type.id,
        "email": "test@test.com",
        "count": "10",
        "expires": expirations[0],
        "notes": "2%",
    }

    resp = admin_client.post("/admin/spawn", data)
    assert resp.status_code == 302

    # Make sure emails are sent out
    assert len(mail.outbox) == 10


def test_coupon_spawn_protected(client) -> None:
    resp = client.get("/admin/spawn")
    assert resp.status_code == 302  # Redirect to login


def test_coupon_flight(client, sample_coupon_type) -> None:
    # GIVEN
    sample_coupon_type.print_template = "flight"
    order = models.Order.from_type(sample_coupon_type)
    order.save()
    coupons = order.process(paid_amount=32.4, paid_currency="EUR")
    assert len(coupons) == 1
    cid = coupons[0].id

    # WHEN
    resp = client.get(f"/coupon/{cid}")

    # THEN
    assert cid.encode("utf-8") in resp.content


def test_coupon_courses(client, sample_coupon_type) -> None:
    # GIVEN
    sample_coupon_type.print_template = "courses"
    order = models.Order.from_type(sample_coupon_type)
    order.save()
    coupons = order.process(paid_amount=32.4, paid_currency="EUR")
    assert len(coupons) == 1
    cid = coupons[0].id

    # WHEN
    resp = client.get(f"/coupon/{cid}")

    # THEN
    assert cid.encode("utf-8") in resp.content


def test_coupon_qr(client, sample_coupon_type) -> None:
    # GIVEN
    order = models.Order.from_type(sample_coupon_type)
    order.save()
    coupons = order.process(paid_amount=32.4, paid_currency="EUR")
    assert len(coupons) == 1
    cid = coupons[0].id

    resp = client.get(f"/coupon/{cid}/qr")

    assert resp.status_code == 200
    assert resp.get("Content-Type") == "image/png"
    assert resp.content[:4], b"\x89PNG"


def test_admin_list(admin_client, sample_coupon_type) -> None:
    # Pre-generate some coupons
    models.Coupon.spawn(
        sample_coupon_type, count=3, email="test@test.com", expires=date.today()
    )

    resp = admin_client.get("/admin/list")
    assert resp.status_code == 200
    assert b"Test Flight" in resp.content
    assert b"test@test.com" in resp.content


def test_admin_list_empty(admin_client, db) -> None:
    resp = admin_client.get("/admin/list")
    assert resp.status_code == 200


def test_admin_summary(admin_client, sample_coupon_type) -> None:
    # GIVEN
    coupons = models.Coupon.spawn(
        sample_coupon_type,
        count=3,
        email="test@test.com",
        expires=date.today() + timedelta(1),
    )
    coupons[0].use()

    # WHEN
    resp = admin_client.get("/admin/")
    assert resp.status_code == 200


def test_admin_check(admin_client, sample_coupon_type) -> None:
    # GIVEN
    coupons = models.Coupon.spawn(
        sample_coupon_type, count=3, email="test@test.com", expires=date.today()
    )
    cid = coupons[0].id

    # WHEN
    resp = admin_client.get(f"/admin/check/{cid}")

    # THEN
    assert resp.status_code == 200
    assert b"Kvietimas galioja." in resp.content


def test_admin_check_use(admin_client, sample_coupon_type) -> None:
    # GIVEN
    coupons = models.Coupon.spawn(
        sample_coupon_type, count=3, email="test@test.com", expires=date.today()
    )
    cid = coupons[0].id

    # WHEN
    resp = admin_client.post(f"/admin/check/{cid}/actions", {"use": ""})
    assert resp.status_code == 302

    coupon = models.Coupon.objects.get(id=cid)
    assert not coupon.active


def test_admin_check_resend(mailoutbox, admin_client, sample_coupon_type) -> None:
    # GIVEN
    coupons = models.Coupon.spawn(
        sample_coupon_type, count=3, email="test@test.com", expires=date.today()
    )
    cid = coupons[0].id

    # WHEN
    resp = admin_client.post(f"/admin/check/{cid}/actions", {"resend": ""})
    assert resp.status_code == 302

    assert len(mail.outbox) == 1
