# Generated by Django 2.2.6 on 2019-10-27 09:39

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("coupons", "0002_auto_20191026_2116")]

    operations = [
        migrations.AddField(
            model_name="coupontype",
            name="deafult_expiration_date",
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="coupontype",
            name="validity_cond_text",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="coupontype",
            name="welcome_text",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
    ]
