from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from . import util


def index(request):
    query_str = request.GET.get('q', None)
    
    if query_str is not None:
        return search_entry(request, query_str)
    
    else:
        return render(request, "encyclopedia/index.html", {
            "entries": util.list_entries()
        })

def entry_page(request, title: str):
    entry_file = util.get_entry(title)
    if entry_file is None:
        return HttpResponseNotFound()
    
    html = util.markdown_to_html(entry_file)
    return render(request, "encyclopedia/entry.html", {
        "entry_title": title,
        "entry_body": html
    })

def search_entry(request, query_str):
    entries = util.list_entries()
    if query_str in entries:
        return HttpResponseRedirect(reverse('wiki:entry_page', args=[query_str]))
    
    else:
        candidates = [e for e in entries if e.lower().find(query_str.lower()) != -1]
        return render(request, "encyclopedia/index.html", {
            "query_str": query_str,
            "entries": candidates
        })
        