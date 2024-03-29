# Generated by Django 3.0.5 on 2020-04-22 17:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coupons", "0005_auto_20191109_1453"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScheduledDiscount",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_from", models.DateTimeField()),
                ("date_to", models.DateTimeField()),
                ("discount", models.IntegerField()),
                ("comment", models.TextField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name="order",
            name="discount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name="coupontype",
            name="price",
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name="order",
            name="paid_amount",
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="price",
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
