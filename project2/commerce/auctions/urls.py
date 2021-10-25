from collections import namedtuple
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("listings/new", views.new_listing, name="new_listing"),
    path("listings/<int:listing_id>", views.listing, name="listing"),
    path("listings/<int:listing_id>/edit", views.edit_listing, name="edit_listing"),
    path("listings/<int:listing_id>/close-auction", views.close_auction, name="close_auction"),
    path("listings/<int:listing_id>/new-bid", views.new_bid, name="new_bid"),
    path("listings/<int:listing_id>/post-comment", views.post_comment, name="post_comment"),
    path("categories", views.categories, name="categories"),
    path("categories/<str:category>", views.category, name="category"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("watchlist/<int:listing_id>/add", views.add_to_watchlist, name="add_to_watchlist"),
    path("watchlist/<int:listing_id>/remove", views.remove_from_watchlist, name="remove_from_watchlist"),
    path("activity", views.activity, name="activity")
]
