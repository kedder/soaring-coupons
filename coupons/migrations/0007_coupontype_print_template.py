# Generated by Django 3.1.4 on 2020-12-13 12:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coupons", "0006_auto_20200422_1749"),
    ]

    operations = [
        migrations.AddField(
            model_name="coupontype",
            name="print_template",
            field=models.CharField(
                choices=[("flight", "Flight Coupon")], default="flight", max_length=32
            ),
            preserve_default=False,
        ),
    ]
