# Generated by Django 3.1.7 on 2021-03-12 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_customer_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='image',
            field=models.ImageField(default='../static/images/user_icon.png', upload_to='../static/images'),
        ),
    ]
