from typing import Sequence
import logging
import pytz
import random
import string
import itertools
from datetime import date, datetime
from decimal import Decimal

from django.db import models

log = logging.getLogger(__name__)

SEASON_START_MONTH = 4
SEASON_END_MONTH = 10


class CouponType(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=255)
    welcome_text = models.TextField(null=True)
    validity_cond_text = models.CharField(max_length=255, null=True)
    deafult_expiration_date = models.DateField()
    in_stock = models.BooleanField(default=True)
    # Template to use when printing the coupon. Will use django template in
    # `templates/coupons/{}.html`
    print_template = models.CharField(
        max_length=32,
        choices=[("flight", "Flight Coupon"), ("courses", "Courses Coupon")],
    )

    def __str__(self) -> str:
        return self.title


class Order(models.Model):
    ST_PENDING = 1
    ST_PAID = 2
    ST_CANCELLED = 3
    ST_SPAWNED = 4

    coupon_type = models.ForeignKey(CouponType, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=8)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    paid_currency = models.CharField(max_length=8, null=True)
    payer_name = models.CharField(max_length=255, null=True)
    payer_surname = models.CharField(max_length=255, null=True)
    payer_email = models.CharField(max_length=255, null=True)
    payment_provider = models.CharField(max_length=255, null=True)
    test = models.BooleanField(default=False)
    status = models.IntegerField(
        choices=[
            (ST_PENDING, "Pending"),
            (ST_PAID, "Paid"),
            (ST_CANCELLED, "Cancelled"),
            (ST_SPAWNED, "Spawned"),
        ],
        default=ST_PENDING,
    )
    create_time = models.DateTimeField()
    payment_time = models.DateTimeField(null=True)
    notes = models.CharField(max_length=255, null=True)

    @classmethod
    def from_type(cls, coupon_type: CouponType, quantity: int = 1) -> "Order":
        return Order(
            coupon_type=coupon_type,
            quantity=quantity,
            price=coupon_type.price,
            currency="EUR",
            create_time=datetime.now(pytz.utc),
        )

    def apply_discount(self, discount: int) -> None:
        new_price = self.price * (1 - discount / Decimal("100"))
        new_price = round(new_price, 2)
        self.discount = self.price - new_price
        self.price = new_price
        log.info(
            f"Applied {discount}% discount ({self.discount} {self.currency}) "
            f"to order {self.id}"
        )

    def process(
        self,
        *,
        paid_amount: float,
        paid_currency: str,
        payer_email: str = None,
        payer_name: str = None,
        payer_surname: str = None,
        payment_provider: str = None,
    ) -> Sequence["Coupon"]:
        """Process order payment.

        Updates order with supplied information and updates status to ST_PAID.
        Creates Coupon object.  Payment information must be validated before
        passing to this method.
        """
        if self.status != Order.ST_PENDING:
            raise ValueError(f"Cannot process non-pending order {self.id}")

        self.paid_amount = paid_amount
        self.paid_currency = paid_currency
        self.payer_email = payer_email
        self.payer_name = payer_name
        self.payer_surname = payer_surname
        self.status = Order.ST_PAID
        self.payment_time = datetime.now(pytz.utc)
        self.payment_provider = payment_provider
        self.save()
        log.info("Order %s processed" % self.id)

        # create coupon
        assert self.quantity == 1
        return Coupon.from_order(self)

    def find_coupons(self) -> Sequence["Coupon"]:
        return list(Coupon.objects.filter(order=self))

    @property
    def paid(self) -> bool:
        return self.status == Order.ST_PAID


class Coupon(models.Model):
    ST_ACTIVE = 1
    ST_USED = 2

    id = models.CharField(max_length=12, primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    year = models.IntegerField()
    status = models.IntegerField(
        choices=[(ST_ACTIVE, "Active"), (ST_USED, "Used")], default=ST_ACTIVE
    )
    use_time = models.DateTimeField(null=True, blank=True)
    expires = models.DateField(null=True, blank=True)

    @staticmethod
    def from_order(order: Order, expires: date = None) -> Sequence["Coupon"]:
        """Create couponse for given order"""
        ctype = order.coupon_type
        payment_year = (
            order.payment_time.year if order.payment_time else order.create_time.year
        )

        if expires is None:
            # Come up with sensible expiration date from copon type settings
            expires = ctype.deafult_expiration_date.replace(year=payment_year)
            # If ticket is sold after this year's expiration date, move it to
            # the next year
            if date.today() > expires:
                expires = expires.replace(year=payment_year + 1)

        coupons = []
        for x in range(order.quantity):
            coupon = Coupon(
                id=Coupon.gen_unique_id(),
                order=order,
                year=payment_year,
                expires=expires,
            )
            coupon.save()
            coupons.append(coupon)
            log.info(f"Coupon {coupon.id} created")

        return coupons

    @staticmethod
    def spawn(
        coupon_type: CouponType,
        *,
        count: int,
        email: str,
        expires: date,
        notes: str = None,
    ) -> Sequence["Coupon"]:
        log.info("Spawning %s coupons", count)
        order = Order.from_type(coupon_type, quantity=count)
        order.status = Order.ST_SPAWNED
        order.notes = notes
        order.payer_email = email
        order.payment_time = datetime.now(pytz.utc)
        order.save()

        return Coupon.from_order(order)

    @staticmethod
    def gen_unique_id() -> str:
        # add some random digits to make order ids less predictable
        seed = "".join(random.choice(string.digits) for i in range(10))
        year = date.today().strftime("%y")
        uniqueid = f"{year}{seed}"

        # make sure it is really unique
        for attempt in range(10):
            try:
                Coupon.objects.get(id=uniqueid)
                log.warning(f"Generated coupon id '{uniqueid}' is not unique")
            except Coupon.DoesNotExist:
                return uniqueid

        raise RuntimeError("Cannot generate unique coupon id")

    @staticmethod
    def get_valid_expirations(today, count):
        def seq(start):
            curmonth = today.month + 1
            curyear = start.year
            earliest_month = SEASON_START_MONTH + 3
            while True:
                if curmonth > SEASON_END_MONTH:
                    curyear += 1
                    curmonth = 1

                if curmonth <= earliest_month:
                    curmonth = earliest_month

                yield date(curyear, curmonth, 1)
                curmonth += 1

        return list(itertools.islice(seq(today), 0, count))

    @property
    def active(self):
        expired = self.expires and date.today() > self.expires
        active = self.status == Coupon.ST_ACTIVE
        return active and not expired

    @property
    def coupon_type(self) -> CouponType:
        return self.order.coupon_type

    def use(self) -> None:
        if not self.active:
            raise ValueError(f"Cannot use non-active coupon {self.id}")

        self.status = Coupon.ST_USED
        self.use_time = datetime.now(pytz.utc)
        self.save()
        log.info(f"Coupon {self.id} used")


class ScheduledDiscount(models.Model):
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    discount = models.IntegerField()
    comment = models.TextField(null=True)

    @staticmethod
    def find_discount_on(now: datetime) -> int:
        """Return discount in percent (0-100) for given time

        Or 0 if no discount."""
        relevant = ScheduledDiscount.objects.filter(date_from__lte=now, date_to__gt=now)
        # Latest discount takes precedence
        relevant = relevant.order_by("-date_from")
        for sd in relevant:
            return sd.discount

        # No discounts found
        return 0
