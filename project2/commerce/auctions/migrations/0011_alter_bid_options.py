# Generated by Django 3.2.4 on 2021-07-25 16:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0010_alter_bid_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bid',
            options={'ordering': ['-amount']},
        ),
    ]