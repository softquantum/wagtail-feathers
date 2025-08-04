import logging
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.rich_text import LinkHandler
from wagtail.snippets import widgets as wagtailsnippets_widgets
from wagtail.snippets.models import register_snippet

from wagtail_feathers.models import Category, Person
from wagtail_feathers.viewsets import (
    FeathersAuthorshipViewSetGroup,
    FeathersNavigationViewSetGroup,
    FeathersSiteComponentsViewSetGroup,
    FeathersTaxonomyViewSetGroup,
    PersonViewSetGroup,
)

from wagtail_feathers.viewsets import classifier_chooser_viewset

logger = logging.getLogger(__name__)


# Handling external links:
# TODO: Is there another way to do it ?
# === === === === ===


class ExternalLinkHandler(LinkHandler):
    """Custom link handler for external links in Wagtail rich text editor.

    The expand_db_attributes class method takes link attributes from the database,
    extracts the href, and returns an HTML anchor tag with a custom data attribute.
    This allows Wagtail to recognize and render external links with a specific
    markup in rich text content.
    """

    identifier = "external"

    @classmethod
    def expand_db_attributes(cls, attrs):
        href = attrs["href"]

        return f'<a data-rich-text-external-link href="{href}">'


@hooks.register("register_rich_text_features")
def register_link_handler(features):
    features.register_link_type(ExternalLinkHandler)


# Register new icons:
# === === === === ===


@hooks.register("register_icons")
def register_icons(icons):
    from django.template import engines

    from wagtail_feathers.themes import TemplateLoader

    heroicons = []
    django_engine = engines["django"]
    template_loader = TemplateLoader(django_engine.engine)
    
    # Get theme directories
    template_dirs = template_loader.get_dirs()
    
    # Also include fallback loaders' directories
    for loader in template_loader.get_fallback_loaders():
        if hasattr(loader, 'get_dirs'):
            template_dirs.extend(loader.get_dirs())
    
    # Search for icons in all template directories
    for template_dir in template_dirs:
        icons_dir = Path(template_dir) / "wagtail_feathers" / "icons"
        if icons_dir.exists():
            for file in icons_dir.rglob("*.svg"):
                relative_path = file.relative_to(icons_dir)
                template_path = f"wagtail_feathers/icons/{relative_path}"
                if template_path not in heroicons:
                    heroicons.append(template_path)

    return icons + heroicons


# Additional Admin CSS:
# === === === === ===


@hooks.register("insert_global_admin_css", order=100)
def global_admin_css():
    """Add /static/css/admin.css to the admin."""
    return format_html('<link rel="stylesheet" href="{}">', static("css/feathers_admin.css"))


@hooks.register("insert_global_admin_js", order=100)
def classifier_admin_js():
    """Add Stimulus-based enhanced classifier admin JavaScript."""
    return format_html(
        '<script type="module" src="{}"></script>',
        static("js/feathers_admin.js")
    )


# Tweaking signals:
# === === === === ===

USER_MODEL = settings.AUTH_USER_MODEL

@receiver(post_save, sender=USER_MODEL)
def create_or_update_user_person_profile(sender, instance, created, **kwargs):
    """Signal handler to create or update a Person profile when a User is saved."""
    if created:
        try:
            existing_person = Person.objects.get(email=instance.email, user__isnull=True)
            existing_person.user = instance
            existing_person.first_name = instance.first_name
            existing_person.last_name = instance.last_name
            existing_person.save()
        except Person.DoesNotExist:
            try:
                potential_matches = Person.objects.filter(
                    first_name=instance.first_name, last_name=instance.last_name, user__isnull=True
                )

                if potential_matches.count() == 1 and potential_matches.first().email == "":
                    existing_person = potential_matches.first()
                    existing_person.user = instance
                    existing_person.email = instance.email
                    existing_person.save()

                elif potential_matches.count() > 1:
                    person_ids = list(potential_matches.values_list("id", flat=True))
                    error_msg = (
                        f"Multiple Person records found with name '{instance.first_name} {instance.last_name}'. "
                        f"Manual linking required for user {instance.id} ({instance.email}). "
                        f"Possible matches: {person_ids}"
                    )
                    logger.warning(error_msg)
                else:
                    Person.objects.create(
                        user=instance,
                        first_name=instance.first_name,
                        last_name=instance.last_name,
                        email=instance.email,
                    )

            except (IntegrityError, ValidationError) as e:
                error_msg = (
                    f"Unable to create or update Person profile for user {instance.id} ({instance.email}): {str(e)}"
                )
                logger.error(error_msg)

            except Exception as e:
                error_msg = (
                    f"Unexpected error linking user {instance.id} ({instance.email}) to Person profile: {str(e)}"
                )
                logger.error(error_msg)

    else:
        try:
            person = Person.objects.get(user=instance)
            fields = ["first_name", "last_name", "email"]
            updated = False
            for field in fields:
                if getattr(person, field) != getattr(instance, field):
                    setattr(person, field, getattr(instance, field))
                    updated = True
            if updated:
                person.save()
        except Person.DoesNotExist:
            # TODO: Refactor.  Workaround: Handle case where user exists but no linked Person profile exists
            try:
                existing_person = Person.objects.get(email=instance.email, user__isnull=True)
                existing_person.user = instance
                existing_person.first_name = instance.first_name
                existing_person.last_name = instance.last_name
                existing_person.save()
            except Person.DoesNotExist:
                try:
                    potential_matches = Person.objects.filter(
                        first_name=instance.first_name, last_name=instance.last_name, user__isnull=True
                    )

                    if potential_matches.count() == 1 and potential_matches.first().email == "":
                        existing_person = potential_matches.first()
                        existing_person.user = instance
                        existing_person.email = instance.email
                        existing_person.save()

                    elif potential_matches.count() > 1:
                        person_ids = list(potential_matches.values_list("id", flat=True))
                        error_msg = (
                            f"Multiple Person records found with name '{instance.first_name} {instance.last_name}'. "
                            f"Manual linking required for user {instance.id} ({instance.email}). "
                            f"Possible matches: {person_ids}"
                        )
                        logger.warning(error_msg)
                    else:
                        Person.objects.create(
                            user=instance,
                            first_name=instance.first_name,
                            last_name=instance.last_name,
                            email=instance.email,
                        )

                except (IntegrityError, ValidationError) as e:
                    error_msg = (
                        f"Unable to create or update Person profile for user {instance.id} ({instance.email}): {str(e)}"
                    )
                    logger.error(error_msg)

                except Exception as e:
                    error_msg = (
                        f"Unexpected error linking user {instance.id} ({instance.email}) to Person profile: {str(e)}"
                    )
                    logger.error(error_msg)


# Chooser viewsets:
# === === === === === ===

@hooks.register("register_admin_viewset")
def register_viewset():
    return classifier_chooser_viewset


# TODO: admin notification system to make these warnings more visible to administrators.
# Create a custom Wagtail admin view that displays all Person records that need manual attention.


# Snippet listing buttons:
# === === === === === ===

@hooks.register('register_snippet_listing_buttons')
def category_listing_buttons(snippet, user, next_url=None):
    """Add custom buttons to Category snippet listing."""
    if snippet._meta.model != Category:
        return
    
    # Don't show buttons for hidden root
    if snippet.is_hidden_root():
        return
    
    yield wagtailsnippets_widgets.SnippetListingButton(
        _('Add Child'),
        reverse('wagtailsnippets_wagtail_feathers_category:add_child', args=[snippet.pk]),
        priority=10,
        icon_name='plus'
    )
    
    yield wagtailsnippets_widgets.SnippetListingButton(
        _('Move'),
        reverse('wagtailsnippets_wagtail_feathers_category:move', args=[snippet.pk]),
        priority=20,
        icon_name='resubmit'
    )


# ViewSet registrations:
# === === === === === ===
register_snippet(FeathersNavigationViewSetGroup)
register_snippet(FeathersTaxonomyViewSetGroup)
register_snippet(FeathersAuthorshipViewSetGroup)
register_snippet(PersonViewSetGroup)
register_snippet(FeathersSiteComponentsViewSetGroup)
