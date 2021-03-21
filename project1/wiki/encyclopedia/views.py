import random

from django import forms
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from . import util


class NewEntryForm(forms.Form):
    """Form used for submiting new entry.
    """

    title = forms.CharField(label="Title")
    content =  forms.CharField(label="", widget=forms.Textarea())


def index(request: HttpRequest) -> HttpResponse:
    """View representing index page. If no query parameter 'q',
    lists all available entries. If 'q' parameter specified returns
    result from search_entry function.
    """

    query_str = request.GET.get('q', None)
    
    if query_str is not None:
        return search_entry(request, query_str)
    
    else:
        return render(request, "encyclopedia/index.html", {
            "entries": util.list_entries()
        })


def entry_page(request: HttpRequest, title: str) -> HttpResponse:
    """Returns 'title' entry page. If no such entry, returns 404
    Not Found.
    """

    # sanitized_title = re.sub('_', ' ', title)
    entry_file = util.get_entry(title)
    
    if entry_file is None:
        return render(request, 'encyclopedia/not_found.html', status=404)
    
    html = util.markdown_to_html(entry_file)
    return render(request, "encyclopedia/entry.html", {
        "entry_title": title,
        "entry_body": html
    })


def search_entry(request: HttpRequest, query_str: str) -> HttpResponse:
    """Searches through entries. If exect match exists redirects to that page, else
    renders all entries that contain 'query_str' as substring in their title.
    """

    entries = util.list_entries()
    # if there is an exact match, redirect to that entry page
    if query_str in entries:
        return HttpResponseRedirect(reverse('wiki:entry_page', args=[query_str]))
    
    # otherwise list all entries that have query string as substring
    else:
        candidates = [e for e in entries if e.lower().find(query_str.lower()) != -1]
        return render(request, "encyclopedia/index.html", {
            "query_str": query_str,
            "entries": candidates
        })


def add_entry(request: HttpRequest) -> HttpResponse:
    """If method is GET renders an empty form for creating new
    wiki page. If method is POST and no entry with specified
    title already exists, stores new entry. If an entry with
    given title already exists returns 400 Bad Request response
    and form filled with data that was tried to be submitted
    """

    if request.method == "POST":
        entry_form = NewEntryForm(request.POST)
        
        if entry_form.is_valid():
            title = entry_form.cleaned_data['title']
            
            # if entry with this title already exists, render filled form with an error message
            # return appropriate 'Bad Request' status
            if util.exists_entry(title) is True:
                return render(request, 'encyclopedia/add.html', {
                    "form": entry_form,
                    "existing_title": True
                }, status=400)
            
            # otherwise save the entry
            util.save_entry(title, entry_form.cleaned_data['content'])
            
            # redirect to the newly created page
            return HttpResponseRedirect(reverse('wiki:entry_page', args=[title]))

    # if method GET, return empty form
    return render(request, "encyclopedia/add.html", {
        "form": NewEntryForm()
    })

def edit_entry(request: HttpRequest, title: str) -> HttpResponse:
    """When method is GET, fetches 'title' entry for editing. If method
    is POST, stores edited content of 'title' entry and redirects to that
    entry page.
    """

    if not util.exists_entry(title):
        return render(request, 'encyclopedia/not_found.html', status=404)

    if request.method == 'POST':
        content = request.POST['content']
        util.save_entry(title, content)

        return HttpResponseRedirect(reverse('wiki:entry_page', args=[title]))

    
    content = util.get_entry(title)
    return render(request, 'encyclopedia/edit.html', {
        "entry_title": title,
        "entry_content": content
    })

def random_page(request: HttpRequest) -> HttpResponse:
    """ Redirects to a random entry page
    """
    entries = util.list_entries()
    entry = entries[random.randrange(0, len(entries))]

    return HttpResponseRedirect(reverse('wiki:entry_page', args=[entry]))