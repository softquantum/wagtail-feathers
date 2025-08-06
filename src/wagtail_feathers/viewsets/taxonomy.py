from django import forms
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django_filters import ChoiceFilter
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.snippets.views.snippets import SnippetViewSet

from wagtail_feathers.models import Category, ClassifierGroup


class CategoryMoveForm(forms.Form):
    """Simple form for moving a category to a new parent."""

    new_parent = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Move to root level",
        help_text="Select the new parent category, or leave empty to move to root level.",
    )

    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop("category", None)
        super().__init__(*args, **kwargs)

        if self.category:
            # Exclude the category itself and its descendants to maintain tree integrity
            excluded_ids = [self.category.pk]
            try:
                excluded_ids.extend(self.category.get_descendants().values_list("pk", flat=True))
            except Exception:
                pass  # In case get_descendants fails

            queryset = (
                Category._base_manager.exclude(pk__in=excluded_ids)
                .exclude(name=Category.ROOT_CATEGORY)
                .order_by("path")
            )

            self.fields["new_parent"].queryset = queryset


class CategoryAddChildForm(WagtailAdminModelForm):
    """Form for adding a child category."""

    class Meta:
        model = Category
        fields = ["name", "slug", "icon", "aliases", "live"]
        widgets = {
            "aliases": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop("parent", None)
        super().__init__(*args, **kwargs)
        if self.parent:
            self.fields["name"].help_text = f"Child category under: {self.parent.name}"


class CategoryFilterSet(WagtailFilterSet):
    """Custom filterset for Categories with depth and hierarchy filtering."""

    live = ChoiceFilter(
        field_name="live",
        choices=[(True, _("Live")), (False, _("Disabled"))],
        label=_("Status"),
        empty_label=_("All statuses"),
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Category
        fields = ["live", "depth"]


class CategoryViewSet(SnippetViewSet):
    """Admin viewset for managing Category snippets with tree hierarchy support."""

    model = Category
    icon = "heroicons-folder-outline"
    filterset_class = CategoryFilterSet
    search_fields = ["name"]
    list_per_page = 20
    ordering = ["path"]
    list_display = ["get_name_display", "depth", "aliases", "icon", "live"]
    if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        list_display.append("locale")

    def get_queryset(self, request):
        """Return all categories including tree structure but exclude hidden root from listing."""
        return Category._base_manager.exclude(name=Category.ROOT_CATEGORY).order_by("path")

    def get_urlpatterns(self):
        """Add custom URL patterns for child category management."""
        urlpatterns = super().get_urlpatterns()
        return urlpatterns + [
            path("add-child/<int:parent_id>/", self.add_child_view, name="add_child"),
            path("move/<int:category_id>/", self.move_view, name="move"),
        ]

    def add_child_view(self, request, parent_id):
        """View for adding a child category to a specific parent."""
        parent_category = get_object_or_404(Category, pk=parent_id)

        if request.method == "POST":
            form = CategoryAddChildForm(request.POST, parent=parent_category)
            if form.is_valid():
                try:
                    # Create child category using the tree method
                    child_category = parent_category.add_child_category(
                        name=form.cleaned_data["name"],
                        slug=form.cleaned_data["slug"],
                        icon=form.cleaned_data["icon"],
                        aliases=form.cleaned_data["aliases"],
                        live=form.cleaned_data["live"],
                    )
                    messages.success(
                        request,
                        f"Child category '{child_category.name}' has been created under '{parent_category.name}'",
                    )
                    return redirect(reverse(f"{self.url_namespace}:list"))
                except Exception as e:
                    messages.error(request, f"Error creating child category: {str(e)}")
        else:
            form = CategoryAddChildForm(parent=parent_category)

        context = {
            "form": form,
            "parent_category": parent_category,
            "opts": self.model._meta,
            "title": f"Add child category under '{parent_category.name}'",
        }
        return render(request, "wagtail_feathers/admin/category_add_child.html", context)

    def move_view(self, request, category_id):
        """View for moving a category to a new parent."""
        category = get_object_or_404(Category, pk=category_id)

        if request.method == "POST":
            form = CategoryMoveForm(request.POST, category=category)
            if form.is_valid():
                try:
                    new_parent = form.cleaned_data["new_parent"]

                    if new_parent:
                        # Move to a specific parent
                        category.move_to_parent(new_parent)
                        messages.success(request, f"Category '{category.name}' moved under '{new_parent.name}'")
                    else:
                        # Move to root level
                        category.move_to_root()
                        messages.success(request, f"Category '{category.name}' moved to root level")

                    return redirect(reverse(f"{self.url_namespace}:list"))
                except Exception as e:
                    messages.error(request, f"Error moving category: {str(e)}")
        else:
            form = CategoryMoveForm(category=category)

        context = {
            "form": form,
            "category": category,
            "opts": self.model._meta,
            "title": f"Move category '{category.name}'",
        }
        return render(request, "wagtail_feathers/admin/category_move.html", context)


class ClassifierGroupViewSet(SnippetViewSet):
    """Admin viewset for managing ClassifierGroup snippets in the Wagtail admin interface."""

    model = ClassifierGroup
    menu_label = "Classifiers"
    icon = "list-ul"
    list_filter = ["type"]
    list_display = ["name", "max_selections", "classifiers_list", "type"]

    if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        list_display.append("locale")
