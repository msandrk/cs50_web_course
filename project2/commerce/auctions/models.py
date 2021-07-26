from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    watchlist = models.ManyToManyField('Listing', blank=True, related_name='watchlist_users')


class Listing(models.Model):
    
    LISTING_CATEGORIES = [
        ('FSHN', 'Fashion'),
        ('TYS', 'Toys'),
        ('ELCTRNCS', 'Electronics'),
        ('HM', 'Home'),
        ('SPRTS', 'Sports'),
        ('OTHR', 'Other')
    ]

    title = models.CharField(max_length=64)
    description = models.TextField()
    image_url = models.URLField(blank=True)
    category = models.CharField(max_length=64, choices=LISTING_CATEGORIES, default='OTHR')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_listings")
    starting_price = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        # price = self.starting_price if self.highest_bid is None else self.highest_bid.amount
        price = self.starting_price if not self.bids.exists() else self.bids.first().amount
        return f"{self.title}: ${price}"
    

class Bid(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_bids')
    amount = models.PositiveIntegerField()
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-amount']

    def __str__(self):
        return f"Bidder: {self.bidder}, Listing: {self.listing.title} Bid: ${self.amount}"