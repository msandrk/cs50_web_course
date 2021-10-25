# Generated by Django 3.2.4 on 2021-07-25 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0006_rename_active_listing_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='watchlist',
            field=models.ManyToManyField(blank=True, related_name='watchlist_users', to='auctions.Listing'),
        ),
    ]