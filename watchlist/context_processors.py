from .config import BASE_LINKS

def navbar_data(request):
    return {
        'navigation_links': BASE_LINKS,
    }