from django.contrib import admin

from . import models


@admin.register(models.ScheduledDiscount)
class ScheduledDiscountAdmin(admin.ModelAdmin):
    list_display = ("date_from", "date_to", "discount", "comment")


@admin.register(models.CouponType)
class CouponTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "price", "in_stock")


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "coupon_type",
        "price",
        "discount",
        "paid_amount",
        "payer_email",
        "status",
    )


@admin.register(models.Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("id", "year", "status", "use_time", "expires")
