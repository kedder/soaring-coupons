from datetime import date, datetime, timezone

import pytest

from coupons import models


@pytest.fixture
def sample_coupon_type(db):
    ct = models.CouponType(
        id="sample",
        price=12.3,
        title="Test Flight",
        welcome_text="",
        validity_cond_text="",
        deafult_expiration_date=date.today(),
    )
    ct.save()
    return ct


def test_coupon_type_title() -> None:
    # GIVEN
    ct = models.CouponType(
        price=12.3,
        title="Test Flight",
        welcome_text="",
        validity_cond_text="",
        deafult_expiration_date=date.today(),
    )

    # THEN
    assert str(ct) == "Test Flight"


def test_order_from_type(sample_coupon_type) -> None:
    # WHEN
    order = models.Order.from_type(sample_coupon_type)

    # THEN
    # Order is not saved
    assert order.id is None
    assert order.coupon_type is sample_coupon_type


def test_order_process(sample_coupon_type) -> None:
    # GIVEN
    order = models.Order.from_type(sample_coupon_type)

    # WHEN
    coupons = order.process(
        paid_amount=32.4, paid_currency="EUR", payer_email="test@test.com"
    )

    # THEN
    assert len(coupons) == 1
    assert order.paid


def test_coupon_spawn(sample_coupon_type) -> None:
    # GIVEN
    today = date.today()

    # WHEN
    coupons = models.Coupon.spawn(
        sample_coupon_type, count=3, email="test@test.com", expires=today
    )

    # THEN
    assert len(coupons) == 3

    c0 = coupons[0]
    assert c0.expires == today
    assert not c0.order.paid
    assert c0.coupon_type is sample_coupon_type


def test_coupon_get_valid_expirations_season_start() -> None:
    today = date(2017, 2, 5)

    expirations = models.Coupon.get_valid_expirations(today, 4)
    assert expirations == [
        date(2017, 7, 1),
        date(2017, 8, 1),
        date(2017, 9, 1),
        date(2017, 10, 1),
    ]


def test_coupon_get_valid_expirations_mid_season() -> None:
    today = date(2017, 6, 5)

    expirations = models.Coupon.get_valid_expirations(today, 7)
    assert expirations == [
        date(2017, 7, 1),
        date(2017, 8, 1),
        date(2017, 9, 1),
        date(2017, 10, 1),
        date(2018, 7, 1),
        date(2018, 8, 1),
        date(2018, 9, 1),
    ]


def test_coupon_use(sample_coupon_type) -> None:
    # GIVEN

    today = date.today()

    coupons = models.Coupon.spawn(
        sample_coupon_type, count=1, email="test@test.com", expires=today
    )

    assert len(coupons) == 1
    c = coupons[0]

    assert c.active
    assert c.use_time is None

    # WHEN
    c.use()

    # THEN
    assert not c.active
    assert c.use_time is not None


def test_scheduled_discount_find_discount_on(db) -> None:
    # GIVEN
    d1 = models.ScheduledDiscount(
        date_from=datetime(2020, 1, 1, 20, 14, tzinfo=timezone.utc),
        date_to=datetime(2020, 1, 1, 22, 12, tzinfo=timezone.utc),
        discount=15,
        comment="Test",
    )
    d1.save()

    dt_before = datetime(2020, 1, 1, 1, 1, tzinfo=timezone.utc)
    dt_on = datetime(2020, 1, 1, 20, 14, tzinfo=timezone.utc)
    dt_after = datetime(2020, 1, 1, 22, 12, tzinfo=timezone.utc)

    # WHEN, THEN
    assert models.ScheduledDiscount.find_discount_on(dt_before) == 0
    assert models.ScheduledDiscount.find_discount_on(dt_on) == 15
    assert models.ScheduledDiscount.find_discount_on(dt_after) == 0


def test_scheduled_discount_overlapping(db) -> None:
    # GIVEN
    d1 = models.ScheduledDiscount(
        date_from=datetime(2020, 1, 1, 20, 14, tzinfo=timezone.utc),
        date_to=datetime(2020, 1, 10, 22, 12, tzinfo=timezone.utc),
        discount=15,
        comment="Broad",
    )
    d1.save()

    d2 = models.ScheduledDiscount(
        date_from=datetime(2020, 1, 3, 20, 14, tzinfo=timezone.utc),
        date_to=datetime(2020, 1, 3, 22, 12, tzinfo=timezone.utc),
        discount=20,
        comment="Narrow",
    )
    d2.save()

    dt_broad = datetime(2020, 1, 2, 1, 1, tzinfo=timezone.utc)
    dt_narrow = datetime(2020, 1, 3, 21, 14, tzinfo=timezone.utc)
    dt_after_narrow = datetime(2020, 1, 5, 0, 0, tzinfo=timezone.utc)

    # WHEN, THEN
    assert models.ScheduledDiscount.find_discount_on(dt_broad) == 15
    assert models.ScheduledDiscount.find_discount_on(dt_narrow) == 20
    assert models.ScheduledDiscount.find_discount_on(dt_after_narrow) == 15
