from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render
from django.urls import reverse
from django import forms

from .models import User, Listing, Bid, Comment


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        exclude = ['created', 'owner', 'is_active']

class EditListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'image_url', 'category']

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
            'content': forms.Textarea(
                attrs={'cols': 45, 'rows': 1, 'placeholder': 'Write a comment...'}
                )
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
            }, status=401)
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
            }, status=400)

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            }, status=400)
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required
@require_http_methods(["GET", "POST"])
def new_listing(request: HttpRequest) -> HttpResponse:
    # If method is POST, try to create a new listing based on the submitted form.
    if request.method == "POST":
        form = ListingForm(request.POST)
        
        if not form.is_valid():
            return render(request, 'auctions/new-listing.html', {
                "listing_form": form,
                "error_field_message": next(iter(form.errors.items))
            }, status=400)
        
        listing = form.save(commit=False)
        listing.owner = request.user
        listing.save()
        return HttpResponseRedirect(reverse('listing', args=[listing.id]))
    
    # If method is GET just return the empty form.
    else:
        return render(request, 'auctions/new-listing.html', {
            "listing_form": ListingForm()
        })

@require_http_methods(["GET"])
def listing(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)

        highest_bidder = listing.bids.first().bidder if listing.bids.exists() else None
        # If no previous bids, minimum new bid is equal to the starting price of an item.
        # Else new bid must be at least +1 of the current value.
        min_bid = listing.starting_price if not highest_bidder else listing.bids.first().amount + 1

        on_watchlist = listing.watchlist_users.filter(pk=request.user.id).exists()

        return render(request, 'auctions/listing.html', {
            "listing": listing,
            "min_bid": min_bid,
            "highest_bidder": highest_bidder,
            "on_watchlist": on_watchlist,
            "bidding_form": BiddingForm(auto_id=False, initial={'amount': min_bid}),
            "comment_form": CommentForm(auto_id=False),
            "comments": listing.listing_comments.all()
        })

    except Listing.DoesNotExist:
        return HttpResponseNotFound(f"<strong>NOT FOUND!</strong><br>No listing with an id={listing_id}!")
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError(
            'Sorry! Something went wrong while processing your request, please try again later!'
            )

@login_required
@require_http_methods(["GET", "POST"])
def edit_listing(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)

        if request.user != listing.owner:
            return render(request, 'auctions/error-msg-redirect.html', {
                'msg': 'Cannot edit listings you are not an owner of.',
                'redirect_to': 'listing',
                'redirect_arg': listing_id
            }, status=403)

        if not listing.is_active:
            return render(request, 'auctions/error-msg-redirect.html', {
                'msg': 'Cannot edit a listing for which auction is already closed.',
                'redirect_to': 'listing',
                'redirect_arg': listing_id
            }, status=400)

        if request.method == "POST":
            form = EditListingForm(request.POST)

            if not form.is_valid():
                return render(request, 'auctions/edit_listing.html', {
                    'edit_form': form,
                    'listing_id': listing_id,
                    'error_field_message': next(iter(form.errors.items))
                }, status=400)

            listing.title = form.cleaned_data['title']
            listing.image_url = form.cleaned_data['image_url']
            listing.category = form.cleaned_data['category']
            listing.save()

            return HttpResponseRedirect(reverse('listing', args=[listing_id]))
        else:
            curr_content = {
                'title': listing.title,
                'image_url': listing.image_url,
                'category': listing.category
            }

            return render(request, 'auctions/edit-listing.html', {
                'edit_form': EditListingForm(initial=curr_content),
                'listing_id': listing_id
            })
    except Listing.DoesNotExist:
        return HttpResponseNotFound(f"<strong>NOT FOUND!</strong><br>No listing with an id={listing_id}!")
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError(
            'Sorry! Something went wrong while processing your request, please try again later!'
            )

@login_required
@require_http_methods(["GET"])
def close_auction(request: HttpRequest, listing_id: int) -> HttpResponse:
    """This view is called when an owner of an active listing wishes to close an
    auction and does so following a dedicated link. After a successful closure
    of an auction, user is redirected to the listing.
    """
    try:
        listing = Listing.objects.get(pk=listing_id)

        cntxt = {
            'redirect_to': 'listing',
            'redirect_arg': listing_id
        }
        if request.user != listing.owner:
            cntxt['msg'] =  'Cannot close an auction for listing you are not an owner of!'
            return render(request, 'auctions/error-msg-redirect.html', cntxt, status=403)
        
        if not listing.is_active:
            cntxt['msg'] = 'Auction for this listing was already closed!'
            return render(request, 'auctions/error-msg-redirect.html', cntxt, status=400)
        
        listing.is_active = False
        listing.save()
        return HttpResponseRedirect(reverse('listing', args=[listing.id]))

    except Listing.DoesNotExist:
        return HttpResponseNotFound(f"<strong>NOT FOUND!</strong><br>No listing with an id={listing_id}!")
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError(
            'Sorry! Something went wrong while processing your request, please try again later!'
            )

@login_required
@require_http_methods(["POST"])
def new_bid(request: HttpRequest, listing_id: int) -> HttpResponse:
    """This view is called upon submission of the bidding form on the listing page. If
    bid is succesfully submitted, it redirects to the listing for which the bid was
    made. Else a page with the error message is displayed which will also eventualy
    redirect to the listing page.
    """
    try:
        listing = Listing.objects.get(pk=listing_id)

        cntxt = {
            'redirect_to': 'listing',
            'redirect_arg': listing_id
        }

        if request.user == listing.owner:
            cntxt['msg'] = 'Cannot place a bid for a listing that you are an owner of!'
            return render(request, 'auctions/error-msg-redirect.html', cntxt, status=400)

        form = BiddingForm(request.POST)

        if not form.is_valid():
            cntxt['field'], cntxt['msg'] = form.errors.popitem()
            return render(request, 'auctions/error-msg-redirect.html', cntxt, status=400)

        min_bid = listing.starting_price if not listing.bids.exists() else listing.bids.first().amount + 1
        bid_amount = form.cleaned_data['amount']
        if min_bid >  bid_amount:
            cntxt['msg'] = f'Minimal bid not met! Bid must be at least ${min_bid}'
            return render(request, 'auctions/error-msg-redirect.html', cntxt, status=400)

        else:
            bid = Bid(bidder=request.user, amount=bid_amount, listing=listing)
            bid.save()
    
            return HttpResponseRedirect(reverse('listing', args=[listing.id]))

    except Listing.DoesNotExist:
        return HttpResponseNotFound(f"<strong>NOT FOUND!</strong><br>No listing with an id={listing_id}!")
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError(
            'Sorry! Something went wrong while processing your request, please try again later!'
            )
    except ValueError as e:
        return render(request, 'auctions/error-message.html', {
            'msg': str(e).capitalize(),
            'redirect_to': 'listing',
            'redirect_arg': listing_id
        }, status=400)

@login_required
@require_http_methods(["POST"])
def post_comment(request: HttpRequest, listing_id: int) -> HttpResponse:
    """This view is called upon a submission of comment form on the listing page. If 
    form validation fails, a page with corresponding error message is returned. The
    user is eventually redirected back to the listing page. If form validation is
    successful, the user is also redirected back to the listing page.
    """
    try:
        listing = Listing.objects.get(pk=listing_id)

        form = CommentForm(request.POST)
        
        if not form.is_valid():
            field, err_msg = form.errors.popitem()
            return render(request, 'auctions/error-msg-redirect.html', {
                'field': field,
                'msg': err_msg,
                'redirect_to': 'listing',
                'redirect_arg': listing_id
            }, status=400)
        
        comment = form.save(commit=False)
        comment.owner = request.user
        comment.listing = listing
        comment.save()
    
        return HttpResponseRedirect(reverse('listing', args=[listing_id]))

    except Listing.DoesNotExist:
        return HttpResponseNotFound(f"<strong>NOT FOUND!</strong><br>No listing with an id={listing_id}!")
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError(
            'Sorry! Something went wrong while processing your request, please try again later!'
            )


@require_http_methods(["GET"])
def categories(request: HttpRequest) -> HttpResponse:
    return render(request, "auctions/categories.html", {
        "categories": [(label.lower(), name) for label, name in Listing.LISTING_CATEGORIES]
    })

@require_http_methods("GET")
def category(request: HttpRequest, category: str) -> HttpResponse:
    all_categories = { id: name for id, name in Listing.LISTING_CATEGORIES }
    category = category.upper()

    if category not in all_categories:
        return HttpResponseNotFound(f"<strong>NOT FOUND!</strong><br>No category with an id={category.lower()}!")
    
    name = all_categories[category]
    return render(request, 'auctions/category.html', {
        "title": name,
        "listings": Listing.objects.filter(is_active=True).filter(category=category)
    })

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
        if request.user == listing.owner:
            return render(request, 'auctions/error-msg-redirect.html', {
                'msg': 'Cannot this listing to the watchlist, you are the owner of it.',
                'redirect_to': 'listing',
                'redirect_arg': listing_id
            }, status=400)
        request.user.watchlist.add(listing)
        return HttpResponseRedirect(reverse('listing', args=[listing_id]))
    except Listing.DoesNotExist:
        return HttpResponseNotFound(f"<strong>NOT FOUND!</strong><br>No listing with an id={listing_id}!")
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError(
            'Sorry! Something went wrong while processing your request, please try again later!'
            )

@login_required
@require_http_methods(["GET"])
def remove_from_watchlist(request: HttpRequest, listing_id: int) -> HttpResponse:
    try:
        listing = Listing.objects.get(pk=listing_id)
        request.user.watchlist.remove(listing)
        return HttpResponseRedirect(reverse('listing', args=[listing_id]))
    except Listing.DoesNotExist:
        return HttpResponseNotFound(f"<strong>NOT FOUND!</strong><br>No listing with an id={listing_id}!")
    except Listing.MultipleObjectsReturned:
        return HttpResponseServerError(
            'Sorry! Something went wrong while processing your request, please try again later!'
            )

@login_required
@require_http_methods(["GET"])
def activity(request: HttpRequest) -> HttpResponse:
    owned_listings = Listing.objects.filter(owner=request.user)
    bidded_listings = { bid.listing for bid in Bid.objects.filter(bidder=request.user) }
    return render(request, 'auctions/activity.html', {
        "owned_listings": owned_listings,
        "bidded_listings": bidded_listings
    })
    