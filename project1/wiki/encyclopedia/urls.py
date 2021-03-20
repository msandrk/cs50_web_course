from django.urls import path

from . import views

app_name = "wiki"
urlpatterns = [
    path("", views.index, name="index"),
    path("add", views.add_entry, name="add_entry"),
    path("wiki/<str:title>", views.entry_page, name="entry_page"),
]
