from django import forms
from django.http import HttpResponseNotFound, HttpResponseRedirect, HttpResponseBadRequest, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from . import util


class NewEntryForm(forms.Form):
    title = forms.CharField(label="Title")
    content =  forms.CharField(label="", widget=forms.Textarea())


def index(request: HttpRequest) -> HttpResponse:
    query_str = request.GET.get('q', None)
    
    if query_str is not None:
        return search_entry(request, query_str)
    
    else:
        return render(request, "encyclopedia/index.html", {
            "entries": util.list_entries()
        })


def entry_page(request: HttpRequest, title: str) -> HttpResponse:
    entry_file = util.get_entry(title)
    
    if entry_file is None:
        return HttpResponseNotFound()
    
    html = util.markdown_to_html(entry_file)
    return render(request, "encyclopedia/entry.html", {
        "entry_title": title,
        "entry_body": html
    })

def search_entry(request: HttpRequest, query_str: str) -> HttpResponse:
    # if there is an exact match, redirect to that entry page
    if util.exists_entry(query_str):
        return HttpResponseRedirect(reverse('wiki:entry_page', args=[query_str]))
    
    # otherwise list all entries that have query string as substring
    else:
        candidates = [e for e in util.list_entries() if e.lower().find(query_str.lower()) != -1]
        return render(request, "encyclopedia/index.html", {
            "query_str": query_str,
            "entries": candidates
        })


def add_entry(request: HttpRequest) -> HttpResponse:

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