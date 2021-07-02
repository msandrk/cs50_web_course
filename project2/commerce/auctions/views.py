from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render
from django.urls import reverse
from django import forms

from .models import User, Listing


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        exclude = ['created', 'owner', 'active', 'highest_bid']
    

def index(request: HttpRequest) -> HttpResponse:
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(active=True)
    })


def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def listing(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)
        
        return render(request, 'auctions/listing.html', {
        "listing": Listing.objects.get(pk=listing_id)
        })
    except Listing.DoesNotExist:
        return HttpResponseNotFound('No such listing!')
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError('Sorry! Something bad happened, please try again later!')

@login_required
def new_listing(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ListingForm(request.POST)
        listing = form.save(commit=False)
        listing.owner = request.user
        listing.save()
        return HttpResponseRedirect(reverse('listing', args=[listing.id]))
    return render(request, 'auctions/new-listing.html', {
        "listing_form": ListingForm()
    })

def categories(request: HttpRequest) -> HttpResponse:
    return render(request, "auctions/categories.html", {
        "categories": [(label.lower(), name) for label, name in Listing.LISTING_CATEGORIES]
    })

def category(request: HttpRequest, category: str) -> HttpResponse:
    category_ids, category_names = zip(*Listing.LISTING_CATEGORIES)
    category = category.upper()

    if category not in category_ids:
        return HttpResponseNotFound("No such category!")
    
    name = category_names[list(category_ids).index(category)]
    return render(request, 'auctions/category.html', {
        "title": name,
        "listings": Listing.objects.filter(active=True).filter(category=category)
    })