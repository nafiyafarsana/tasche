# Generated by Django 4.1.1 on 2022-10-08 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_order_pincode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='pincode',
            field=models.CharField(max_length=15, null=True),
        ),
    ]