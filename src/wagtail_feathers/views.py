from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import bad_request as django_400
from django.views.defaults import page_not_found as django_404
from django.views.defaults import permission_denied as django_403
from django.views.defaults import server_error as django_500
from django.views.generic import TemplateView

from wagtail_feathers.models import ErrorPage


class ErrorPageTemplateView(TemplateView):
    """Inject Wagtail error page content in Template view if available."""
    
    error_code = None

    def get(self, request, *args, **kwargs):
        if self.error_code:
            error_page = ErrorPage.get_error_page(self.error_code)
            if error_page:
                request.error_page = error_page
        return super().get(request, *args, **kwargs)



# These views can be called when CsrfViewMiddleware.process_view() not run,
# therefore need @requires_csrf_token in case the template needs
# {% csrf_token %}.

@requires_csrf_token
def error_400_view(request, exception, template_name='400.html'):
    """400 handler that injects Wagtail error page content if available."""
    error_page = ErrorPage.get_error_page('400')

    if error_page:
        request.error_page = error_page

    return django_400(request, exception, template_name)


@requires_csrf_token
def error_403_view(request, exception, template_name='403.html'):
    """403 handler that injects Wagtail error page content if available."""
    error_page = ErrorPage.get_error_page('403')

    if error_page:
        request.error_page = error_page

    return django_403(request, exception, template_name)


@requires_csrf_token
def error_404_view(request, exception, template_name='404.html'):
    """404 handler that injects Wagtail error page content if available."""
    error_page = ErrorPage.get_error_page('404')

    if error_page:
        request.error_page = error_page

    return django_404(request, exception, template_name)


@requires_csrf_token
def error_500_view(request, template_name='500.html'):
    """500 handler that injects Wagtail error page content if available."""
    error_page = ErrorPage.get_error_page('500')

    if error_page:
        request.error_page = error_page

    return django_500(request, template_name)
