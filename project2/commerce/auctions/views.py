from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError, HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse
from django import forms

from .models import User, Listing, Bid


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        exclude = ['created', 'owner', 'active', 'highest_bid']

@require_http_methods(["GET"])
def index(request: HttpRequest) -> HttpResponse:
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(active=True)
    })

@require_http_methods(["GET", "POST"])
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

@require_http_methods(["GET"])
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return HttpResponseRedirect(reverse("index"))

@require_http_methods(["GET", "POST"])
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

@require_http_methods(["GET"])
def listing(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)
        
        no_prev_bids = listing.highest_bid is None
        
        return render(request, 'auctions/listing.html', {
            "listing": Listing.objects.get(pk=listing_id),
            "min_bid": listing.starting_price if no_prev_bids else listing.highest_bid.amount + 1,
            "no_prev_bids": no_prev_bids
        })
    except Listing.DoesNotExist:
        return HttpResponseNotFound('No such listing!')
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError('Sorry! Something bad happened, please try again later!')

@require_http_methods(["GET", "POST"])
@login_required
def new_listing(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ListingForm(request.POST)
        
        if not form.is_valid():
            return render(request, 'auctions/new-listing.html', {
                "listing_form": form,
                "error_field_message": next(iter(form.errors.items))
            })
        listing = form.save(commit=False)
        listing.owner = request.user
        listing.save()
        return HttpResponseRedirect(reverse('listing', args=[listing.id]))
    else:
        return render(request, 'auctions/new-listing.html', {
            "listing_form": ListingForm()
        })

@require_http_methods(["GET"])
def categories(request: HttpRequest) -> HttpResponse:
    return render(request, "auctions/categories.html", {
        "categories": [(label.lower(), name) for label, name in Listing.LISTING_CATEGORIES]
    })

@require_http_methods("GET")
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

@require_http_methods(["POST"])
@login_required
def new_bid(request: HttpRequest, listing_id: int) -> HttpResponse:    
    listing = Listing.objects.filter(pk=listing_id).first()
    if listing is None:
        return render(request, "auctions/not-found.html", {
            "message": "No such listing."
        }, status=404)

    try:
        bid_amount = int(request.POST['bid_amount'])
    except ValueError:
        return HttpResponseBadRequest(f"Bid must be an integer, {request.POST['bid_amount']} is not an integer")
    
    min_bid = listing.starting_price if listing.highest_bid is None else listing.highest_bid.amount + 1

    if min_bid <= bid_amount:
        bid = Bid(bidder=request.user, amount=bid_amount)
        listing.highest_bid = bid
        bid.save()
        listing.save()

        return HttpResponseRedirect(reverse('listing', args=[listing.id]))

    else:
        return HttpResponseBadRequest(content=f"Minimum bid not met! Bid must be at least {min_bid}")

@login_required
@require_http_methods(["GET"])
def watchlist(request: HttpRequest) -> HttpResponse:
    return render(request, 'auctions/watchlist.html', {
        'listings': request.user.watchlist
    })

@login_required
# @require_http_methods(["POST"])
def add_to_watchlist(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)

        request.user.watchlist.add(listing)
        return HttpResponseRedirect(reverse('listing', args=[listing_id]))
    except Listing.DoesNotExist:
        return HttpResponseNotFound('No such listing!')
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError('Sorry! Something bad happened, please try again later!')

@login_required
def remove_from_watchlist(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)

        request.user.watchlist.remove(listing)
        return HttpResponseRedirect(reverse('listing', args=[listing_id]))
    except Listing.DoesNotExist:
        return HttpResponseNotFound('No such listing')
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError('Sorry! Something bad happened, please try again later!')