from django.http import HttpResponseNotFound
from django.shortcuts import render

from . import util


def index(request):
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