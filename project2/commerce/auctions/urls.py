from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("listings/<int:listing_id>", views.listing, name="listing"),
    path("new", views.new_listing, name="new_listing"),
    path("categories", views.categories, name="categories"),
    path("categories/<str:category>", views.category, name="category")
]
