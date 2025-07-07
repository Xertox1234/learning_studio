from django.shortcuts import render


def community_index_view(request):
    """Community index page."""
    context = {}
    return render(request, 'community/index.html', context)
