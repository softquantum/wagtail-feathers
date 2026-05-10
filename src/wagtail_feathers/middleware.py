from asgiref.sync import iscoroutinefunction
from django.utils.decorators import sync_and_async_middleware

from .themes import _current_site, set_current_site


@sync_and_async_middleware
def theme_site_middleware(get_response):
    """Bind the current request's Wagtail Site to a ContextVar for the theme system.

    Required for per-site theming to work at the template loader and static finder
    layer. Without this middleware, those layers fall back to the default site.

    Must be ordered after any middleware that resolves the request's site (e.g.
    Wagtail's SiteMiddleware, if used). It is async-aware and works under both
    WSGI and ASGI.
    """
    from wagtail.models import Site

    if iscoroutinefunction(get_response):
        async def middleware(request):
            site = Site.find_for_request(request)
            token = set_current_site(site)
            try:
                return await get_response(request)
            finally:
                _current_site.reset(token)
    else:
        def middleware(request):
            site = Site.find_for_request(request)
            token = set_current_site(site)
            try:
                return get_response(request)
            finally:
                _current_site.reset(token)

    return middleware
