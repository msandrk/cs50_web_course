from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.forms import widgets
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django import forms

from .models import User, Listing, Bid, Comment


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        exclude = ['created', 'owner', 'is_active']

class BiddingForm(forms.ModelForm):
    
    class Meta:
        model = Bid
        fields = ['amount']
        labels = {
            'amount': ''
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        labels = {
            'content': ''
        }
        widgets = {
            'content': forms.Textarea(attrs={'cols': 45, 'rows': 1.5, 'placeholder': 'Write a comment...'})
        }

@require_http_methods(["GET"])
def index(request: HttpRequest) -> HttpResponse:
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(is_active=True)
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

@require_http_methods(["GET", "POST"])
def listing(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)

        no_prev_bids = not listing.bids.exists()

        min_bid = listing.starting_price if no_prev_bids else listing.bids.first().amount + 1

        on_watchlist = listing.watchlist_users.filter(pk=request.user.id).exists()

        cntxt = {
            "listing": listing,
            "min_bid": min_bid,
            "no_prev_bids": no_prev_bids,
            "on_watchlist": on_watchlist,
            "bidding_form": BiddingForm(auto_id=False, initial={'amount': min_bid}),
            "comment_form": CommentForm(auto_id=False),
            "comments": listing.listing_comments.all()
        }

        if request.method == "GET":
            return render(request, 'auctions/listing.html', cntxt)
        
        elif request.method == "POST":
            try:
                form = BiddingForm(request.POST)
                
                if not form.is_valid():
                    cntxt["bidding_form"] = form
                    return render(request, "auctions/listing.html", cntxt, status=500)
                
                bid_amount = form.cleaned_data['amount']
                if min_bid >  bid_amount:
                    form.add_error('amount', f'Minimal bid not met! Bid must be at least ${min_bid}')
                    cntxt['bidding_form'] = form
                    return render(request, "auctions/listing.html", cntxt, status=500)

                else:
                    bid = Bid(bidder=request.user, amount=bid_amount, listing=listing)
                    bid.save()
            
                    return HttpResponseRedirect(reverse('listing', args=[listing.id]))

            except ValueError:
                return render(request, 'auctions/listing.html', cntxt, status=500)

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

@login_required
def close_auction(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)
        listing.is_active = False
        listing.save()
        return HttpResponseRedirect(reverse('listing', args=[listing.id]))
    except Listing.DoesNotExist:
        return HttpResponseNotFound('No such listing.')
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError('Oops! Something bad happened, please try again later!')

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
        "listings": Listing.objects.filter(is_active=True).filter(category=category)
    })


@login_required
@require_http_methods(["POST"])
def post_comment(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)

        form = CommentForm(request.POST)
        
        if not form.is_valid():
            pass
        
        comment = form.save(commit=False)
        comment.owner = request.user
        comment.listing = listing
        comment.save()
    
        return HttpResponseRedirect(reverse('listing', args=[listing_id]))

    except Listing.DoesNotExistError:
        return HttpResponseNotFound('No listing with specified id')
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError('Sorry! Something bad happened, please try again later!')

@login_required
@require_http_methods(["GET"])
def watchlist(request: HttpRequest) -> HttpResponse:
    return render(request, 'auctions/watchlist.html', {
        'listings': request.user.watchlist.all()
    })

@login_required
@require_http_methods(["GET"])
def add_to_watchlist(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)
        print(f"\nadd_to_watchlist: {request.method}\n")
        request.user.watchlist.add(listing)
        return HttpResponseRedirect(reverse('listing', args=[listing_id]))
    except Listing.DoesNotExist:
        return HttpResponseNotFound('No such listing!')
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError('Sorry! Something bad happened, please try again later!')

@login_required
@require_http_methods(["GET"])
def remove_from_watchlist(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)
        print(f"\nremove_from_watchlist: {request.method}\n")
        request.user.watchlist.remove(listing)
        return HttpResponseRedirect(reverse('listing', args=[listing_id]))
    except Listing.DoesNotExist:
        return HttpResponseNotFound('No such listing')
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError('Sorry! Something bad happened, please try again later!')

@login_required
@require_http_methods(["GET"])
def activity(request: HttpRequest) -> HttpResponse:
    owned_listings = Listing.objects.filter(owner=request.user)
    bidded_listings = {bid.listing for bid in Bid.objects.filter(bidder=request.user)}
    return render(request, 'auctions/activity.html', {
        "owned_listings": owned_listings,
        "bidded_listings": bidded_listings
    })
    