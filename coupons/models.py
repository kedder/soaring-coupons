from datetime import date, datetime

from django.db import models


class CouponType(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    price = models.FloatField()
    title = models.CharField(max_length=255)
    in_stock = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.title


class Order(models.Model):
    ST_PENDING = 1
    ST_PAID = 2
    ST_CANCELLED = 3
    ST_SPAWNED = 4

    coupon_type = models.ForeignKey(CouponType, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    currency = models.CharField(max_length=8)
    paid_amount = models.FloatField(null=True)
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
    notes = models.CharField(max_length=255)

    @classmethod
    def single(cls, coupon_type: CouponType) -> "Order":
        return Order(
            coupon_type=coupon_type,
            quantity=1,
            price=coupon_type.price,
            currency="EUR",
            create_time=datetime.now(),
        )


class Coupon(models.Model):
    ST_ACTIVE = 1
    ST_USED = 2

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    year = models.IntegerField()
    status = models.IntegerField(
        choices=[(ST_ACTIVE, "Active"), (ST_USED, "Used")], default=ST_ACTIVE
    )
    use_time = models.DateTimeField(null=True)
    expires = models.DateField()

    @property
    def active(self):
        expired = self.expires and date.today() > self.expires
        active = self.status == Coupon.ST_ACTIVE
        return active and not expired
