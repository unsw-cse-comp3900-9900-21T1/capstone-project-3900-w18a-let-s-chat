# Generated by Django 3.1.7 on 2021-03-25 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0012_productviewcount_last_viewing'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
