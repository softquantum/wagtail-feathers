from typing import List, Type

from django import forms
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import RichTextBlock
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images import get_image_model
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Collection
from wagtailmarkdown.blocks import MarkdownBlock
from wagtail_feathers.struct_values import LinkStructValue
from wagtail_feathers.themes import get_theme_variants

""" Base Blocks
All custom blocks should inherit from one of these classes.
"""


class ThemeVariantChooserBlock(blocks.FieldBlock):
    """Enables choosing a theme variant in the streamfield.

    Lazy loads the choices from the theme system to avoid initialization issues.

    """

    widget = forms.Select

    def __init__(
        self, component_type=None, required=False, label=None, help_text=None, default=None, *args, **kwargs
    ):
        self.component_type = component_type
        self._required = required
        self._help_text = help_text
        self._label = label
        self._default = default
        super().__init__(*args, **kwargs)

    @cached_property
    def field(self):
        choices = []
        if self.component_type:
            try:
                theme_choices = get_theme_variants(self.component_type)
                if theme_choices:
                    choices = theme_choices
                else:
                    choices = [("default", "Default")]
            except Exception:
                choices = [("default", "Default")]
        else:
            choices = [("default", "Default")]

        return forms.ChoiceField(
            choices=choices,
            widget=self.widget,
            required=self._required,
            label=self._label,
            help_text=self._help_text,
            initial=self._default,
        )

    def to_python(self, value):
        """Convert the serialized value back into a python object."""
        return value

    def get_prep_value(self, value):
        """Serialize the value for storage."""
        return value


class CollectionChooserBlock(blocks.FieldBlock):
    """Enables choosing a wagtail Collection in the streamfield."""

    target_model = Collection
    widget = forms.Select

    def __init__(
        self, required=False, label=None, help_text=None, *args, **kwargs
    ):
        self._required = required
        self._help_text = help_text
        self._label = label
        super().__init__(*args, **kwargs)

    @cached_property
    def field(self):
        return forms.ModelChoiceField(
            queryset=self.target_model.objects.all().order_by("name"),
            widget=self.widget,
            required=self._required,
            label=self._label,
            help_text=self._help_text,
        )

    def to_python(self, value):
        """Convert the serialized value back into a python object."""
        if isinstance(value, int):
            return self.target_model.objects.get(pk=value)
        return value

    def get_prep_value(self, value):
        """Serialize the model in a form suitable for wagtail's JSON-ish streamfield."""
        if isinstance(value, self.target_model):
            return value.pk
        return value


class BaseBlock(blocks.StructBlock):
    """Base block class with theme awareness.

    All custom blocks should inherit from this to get automatic theme variant support.

    This is an abstract base class - child classes MUST define:
        component_type (str): The component type identifier (e.g., "hero", "card", etc.)
        default_variant (str): The default theme variant (usually "default")

    Note:
        Child classes must override component_type to match their theme.json variants.

    """
    max_num = 1
    component_type = None
    default_variant = None

    def __init__(self, local_blocks=None, **kwargs):
        """Add theme variants for this component type."""
        if not local_blocks:
            local_blocks = ()

        if self.component_type:
            local_blocks += (
                (
                    "theme_variant",
                    ThemeVariantChooserBlock(
                        component_type=self.component_type,
                        default=self.default_variant or "default",
                        required=False,
                        label="Theme variant",
                        help_text="Select a theme variant for this component",
                    ),
                ),
            )

        super().__init__(local_blocks, **kwargs)

    class Meta:
        abstract = True


class BaseContainerBlock(BaseBlock):
    """Provide a StreamBlock wrapper.

    It provides flexibility to define and manage these child blocks either
    statically or dynamically based on the specified configurations.

    Attributes:
        content_streamblocks: List of block types that represent the default
            content streamblocks for the container block. This attribute can be
            overridden or expanded in subclasses.

    """

    fluid = blocks.BooleanBlock(
            required=False,
            default=True,
            label=_("Full width"),
    )

    heading = blocks.CharBlock(
        form_classname="title",
        icon="title",
        required=True,
        help_text=_("Use h2 in your template to create a heading."),
    )

    sr_only_label = blocks.BooleanBlock(
        required=False,
        label="Screen reader only label",
        help_text="If checked, the heading will be hidden from view and avaliable to screen-readers only.",
    )

    content_streamblocks: List[Type[blocks.Block]] = []

    def __init__(self, local_blocks=None, **kwargs):
        if not local_blocks and self.content_streamblocks:
            local_blocks = self.content_streamblocks

        if local_blocks:
            local_blocks = (
                (
                    "content",
                    blocks.StreamBlock(local_blocks, label=_("Content")),
                ),
            )

        super().__init__(local_blocks, **kwargs)

    class Meta:
        abstract = True


""" StructBlocks
https://docs.wagtail.org/en/stable/topics/streamfield.html#structblock
StructBlock allows you to group several ‘child’ blocks together to be presented as a single block. 
The child blocks are passed to StructBlock as a list of (name, block_type) tuples.
These new subclasses can then be used in a StreamField definition in the same way as 
the built-in block types.  It adds readability to your StreamField definition.
"""


class ImageBlock(BaseBlock):
    """A block that allows editors to add an image with optional caption and attribution in body section."""
    
    component_type = "image"
    default_variant = "default"

    image = ImageChooserBlock(required=True)
    image_alt_text = blocks.CharBlock(
        required=False,
        help_text=_("If left blank, the image's global alt text will be used."),
    )

    @cached_property
    def preview_image(self):
        # Cache the image object for previews to avoid repeated queries
        image = get_image_model().objects.last()
        if image:
            image.caption = _("A beautiful image")
            image.attribution = "The SoftQantum Library"
        return image

    def get_preview_value(self):
        return {
            **self.meta.preview_value,
            "image": self.preview_image,
        }

    class Meta:
        icon = "image"
        template = "wagtail_feathers/blocks/image_block.html"
        preview_value = {"caption": _("A beautiful image"), "attribution": "The SoftQantum Library"}
        description = _("An image with optional caption and attribution")


class ImageCollectionGalleryBlock(BaseBlock):
    """Show a collection of images with interactive previews that expand to full size images in a modal."""

    collection = CollectionChooserBlock(
        required=True,
        label=_("Image Collection"),
    )

    class Meta:
        template = "wagtail_feathers/blocks/image_collection_gallery_block.html"
        icon = "image"
        label = _("Image Gallery")


class ImageGridBlock(BaseBlock):
    """Show images in a grid that expand to full size images in a modal."""

    images = blocks.ListBlock(
        ImageBlock(),
        label=_("Images"),
        help_text=_("Add images to display in the grid")
    )

    class Meta:
        template = "wagtail_feathers/blocks/image_grid_block.html"
        icon = "image"
        label = _("Image Gallery")


class HeaderImageBlock(BaseBlock):
    """Add an image with optional caption and attribution in a Header section."""

    component_type = "image"
    default_variant = "default"

    fluid = blocks.BooleanBlock(
        required=False,
        default=True,
        label=_("Full width"),
    )
    image = ImageChooserBlock(required=True)
    image_alt_text = blocks.CharBlock(
            required=False,
            help_text=_("If left blank, the image's global alt text will be used."),
    )

    @cached_property
    def preview_image(self):
        image = get_image_model().objects.last()
        if image:
            image.caption = _("A beautiful image")
            image.attribution = "The SoftQantum Library"
        return image

    def get_preview_value(self):
        return {
            **self.meta.preview_value,
            "image": self.preview_image,
        }

    class Meta:
        icon = "image"
        template = "wagtail_feathers/blocks/header_image_block.html"
        preview_value = {"caption": _("A beautiful image"), "attribution": "The SoftQantum Library"}
        description = _("An image with optional caption and attribution")


class HeadingBlock(BaseBlock):
    """A block that allows editors to add a heading with level two, three, or four.


    clean(): Handles form validation and saving
    get_form_state(): Auto-fills heading_id in the admin interface when loading existing content
    get_api_representation(): Ensures API responses always include the heading_id

    """
    
    component_type = "heading"
    default_variant = "default"

    heading_text = blocks.CharBlock(required=True)
    size = blocks.ChoiceBlock(
        choices=[
            ("", _("Select a header size")),
            ("h2", "H2"),
            ("h3", "H3"),
            ("h4", "H4"),
            ("h5", "H5"),
            ("h6", "H6"),
        ],
        blank=True,
        required=False,
    )

    class Meta:
        icon = "title"
        template = "wagtail_feathers/blocks/heading_block.html"
        preview_value = {"heading_text": _("A beautiful weather today"), "size": "h2"}
        description = _("A heading with level two, three, or four")


class QuoteBlock(BaseBlock):
    """A block that allows editors to add a quote with optional attribution."""
    
    component_type = "quote"
    default_variant = "default"

    quote = blocks.RichTextBlock(required=True)
    attribution = blocks.CharBlock(blank=True, required=False, label="e.g. Maxime Decooman")

    class Meta:
        icon = "openquote"
        template = "wagtail_feathers/blocks/quote_block.html"
        preview_value = {"quote": _("Believe you can and you're halfway there."), "attribution": "Theodore Roosevelt"}
        description = _("A quote with an optional attribution")


class InternalLinkBlock(blocks.StructBlock):
    """A block that allows editors to add a link of type internal."""

    page = blocks.PageChooserBlock(required=False)
    document = DocumentChooserBlock(required=False)
    title = blocks.CharBlock(
        required=False,
        help_text="Leave blank to use link's title.",
    )

    class Meta:
        icon = "link"
        value_class = LinkStructValue


class ExternalLinkBlock(blocks.StructBlock):
    """A block that allows editors to add a link of type external."""

    link = blocks.URLBlock()
    title = blocks.CharBlock(required=False)
    link_target = blocks.BooleanBlock(
        required=False,
        help_text=_("Open the link in a new tab"),
    )

    class Meta:
        icon = "link"
        value_class = LinkStructValue


class PageHeadingBlock(BaseBlock):
    """A block that allows editors to add a page heading and subheading."""

    component_type = "heading"
    default_variant = "default"

    fluid = blocks.BooleanBlock(
        required=False,
        default=True,
        label=_("Full width"),
    )
    heading = RichTextBlock(features=["bold", "italic"], required=False)
    sub_heading = blocks.CharBlock(label="Sub Heading", max_length=120, required=False)
    alignment = blocks.ChoiceBlock(
        choices=[
            ("left", _("Left")),
            ("center", _("Center")),
            ("right", _("Right")),
        ],
        default="center",
        help_text=_("Text alignment for the hero content")
    )
    class Meta:
        icon = "title"
        template = "wagtail_feathers/blocks/page_heading_block.html"
        label = _("Page Heading")
        preview_value = {
            "heading": _("Welcome to Our Amazing Platform"),
            "sub_heading": _("Transform your workflow with cutting-edge technology"),
            "alignment": "left",
        }
        description = _("A page heading block that can have a heading and subheading")


class HeroBlock(BaseBlock):
    """A hero section block with image, heading, text, and call-to-action buttons."""
    
    component_type = "hero"
    default_variant = "default"

    style_id = blocks.CharBlock(
        max_length=50,
        required=False,
        help_text=_("Optional id for the hero section style"),
    )

    heading = blocks.RichTextBlock(
        max_length=120,
        help_text=_("Main headline for the hero section (max 120 characters)")
    )
    
    sub_heading = blocks.CharBlock(
        max_length=200,
        required=False,
        help_text=_("Optional subheadline or tagline (max 200 characters)")
    )
    
    description = blocks.RichTextBlock(
        required=False,
        features=["bold", "italic", "link"],
        help_text=_("Optional description text with basic formatting")
    )
    
    background_image = ImageChooserBlock(
        required=False,
        help_text=_("Background image for the hero section")
    )
    
    background_image_alt = blocks.CharBlock(
        required=False,
        max_length=100,
        help_text=_("Alt text for background image (for accessibility)")
    )

    call_to_actions = blocks.StreamBlock([
        ("cta", blocks.StructBlock([
            ("text", blocks.CharBlock(max_length=50, help_text=_("Button text"))),
            ("link", blocks.StreamBlock([
                ("internal", InternalLinkBlock()),
                ("external", ExternalLinkBlock()),
            ], max_num=1)),
            ("style", blocks.ChoiceBlock(
                    choices=[
                        ("primary", _("Primary")),
                        ("secondary", _("Secondary")),
                        ("outline", _("Outline")),
                    ],
                    default="primary",
                    help_text=_("Button style")
            ))
        ], label=_("Call-to-Action Button")))
    ], required=False, max_num=3, label=_("Call-to-Action Buttons"),
            help_text=_("Add up to 3 call-to-action buttons"))

    fluid = blocks.BooleanBlock(
        required=False,
        default=True,
        label=_("Full width"),
    )
    
    alignment = blocks.ChoiceBlock(
        choices=[
            ("left", _("Left")),
            ("center", _("Center")),
            ("right", _("Right")),
        ],
        default="center",
        help_text=_("Text alignment for the hero content")
    )
    
    overlay_opacity = blocks.ChoiceBlock(
        choices=[
            ("0", _("No overlay")),
            ("25", _("Light overlay (25%)")),
            ("50", _("Medium overlay (50%)")),
            ("75", _("Dark overlay (75%)")),
            ("85", _("Darker overlay (85%)")),
        ],
        default="25",
        required=False,
        help_text=_("Overlay opacity for better text readability over background image")
    )

    class Meta:
        icon = "heroicons-photo-outline"
        template = "wagtail_feathers/blocks/hero_block.html"
        label = _("Hero Section")
        form_classname = "hero-block-form"
        preview_value = {
            "headline": _("Welcome to Our Amazing Platform"),
            "subheadline": _("Transform your workflow with cutting-edge technology"),
            "description": _("Join thousands of users who have revolutionized their productivity with our innovative solutions."),
            "alignment": "center",
            "overlay_opacity": "25",
            "call_to_actions": [
                {
                    "type": "cta",
                    "value": {
                        "text": _("Get Started"),
                        "link": [],
                        "style": "primary"
                    }
                },
                {
                    "type": "cta",
                    "value": {
                        "text": _("Learn More"),
                        "link": [],
                        "style": "secondary"
                    }
                }
            ]

        }
        description = _("A hero section with headline, description, background image, and call-to-action buttons")


class CardBlock(BaseBlock):
    """A card block with image, heading, text, and optional link."""

    component_type = "card"
    default_variant = "default"

    image = ImageChooserBlock(
            required=False,
            help_text=_("Card image")
    )

    image_alt = blocks.CharBlock(
            required=False,
            max_length=100,
            help_text=_("Alt text for the card image")
    )

    heading = blocks.CharBlock(
            max_length=100,
            help_text=_("Card heading")
    )

    text = blocks.RichTextBlock(
            required=False,
            features=["bold", "italic", "link"],
            help_text=_("Card content text")
    )

    link = blocks.StreamBlock([
        ("internal", InternalLinkBlock()),
        ("external", ExternalLinkBlock()),
    ], required=False, max_num=1, help_text=_("Optional card link"))

    link_text = blocks.CharBlock(
            required=False,
            max_length=50,
            help_text=_("Text for the card link (e.g., 'Read More', 'Learn More')")
    )

    class Meta:
        icon = "heroicons-rectangle-stack-outline"
        template = "wagtail_feathers/blocks/card_block.html"
        label = _("Card")
        preview_value = {
            "heading": _("Feature Card"),
            "text": _("This is a sample card with some description text that showcases the content."),
            "link_text": _("Learn More")
        }
        description = _("A card with optional image, heading, text, and link")


class CallToActionBlock(BaseBlock):
    """A call-to-action block with heading, text, and button."""
    
    component_type = "cta"
    default_variant = "default"

    heading = blocks.CharBlock(
        max_length=100,
        help_text=_("Call-to-action heading")
    )
    
    text = blocks.RichTextBlock(
        required=False,
        features=["bold", "italic"],
        help_text=_("Supporting text for the call-to-action")
    )
    
    button_text = blocks.CharBlock(
        max_length=50,
        help_text=_("Text for the action button")
    )
    
    button_link = blocks.StreamBlock([
        ("internal", InternalLinkBlock()),
        ("external", ExternalLinkBlock()),
    ], max_num=1, help_text=_("Link for the action button"))
    
    background_color = blocks.ChoiceBlock(
        choices=[
            ("default", _("Default")),
            ("primary", _("Primary")),
            ("secondary", _("Secondary")),
            ("accent", _("Accent")),
        ],
        default="primary",
        help_text=_("Background color theme for the CTA section")
    )

    class Meta:
        icon = "heroicons-cursor-arrow-rays-outline"
        template = "wagtail_feathers/blocks/cta_block.html"
        label = _("Call to Action")
        preview_value = {
            "heading": _("Ready to Get Started?"),
            "text": _("Join our community and start your journey today."),
            "button_text": _("Sign Up Now"),
            "background_color": "primary"
        }
        description = _("A call-to-action section with heading, text, and action button")





class CardsContainerBlock(BaseContainerBlock):
    """A container block for displaying multiple cards in a grid layout."""
    
    component_type = "cards_container"
    default_variant = "default"
    
    content_streamblocks = [
        ("card", CardBlock()),
    ]

    def __init__(self, local_blocks=None, **kwargs):
        if not local_blocks:
            local_blocks = (
                ("heading", blocks.CharBlock(
                    required=False,
                    max_length=100,
                    help_text=_("Optional heading for the cards section")
                )),
                ("columns", blocks.ChoiceBlock(
                    choices=[
                        ("1", _("1 Column")),
                        ("2", _("2 Columns")),
                        ("3", _("3 Columns")),
                        ("4", _("4 Columns")),
                    ],
                    default="3",
                    help_text=_("Number of columns for the card grid")
                )),
            )
        super().__init__(local_blocks, **kwargs)

    class Meta:
        icon = "heroicons-squares-2x2-outline"
        template = "wagtail_feathers/blocks/cards_container_block.html"
        label = _("Cards Grid")
        description = _("A container for displaying multiple cards in a grid layout")


class PageMenuBlock(blocks.StructBlock):
    """Block that generates menu items from a page and its children."""

    parent_page = blocks.PageChooserBlock(required=True, help_text=_("Select a page to use its children as menu items"))

    max_levels = blocks.IntegerBlock(
        default=1, min_value=1, max_value=5, help_text=_("Maximum number of levels to show from page hierarchy")
    )

    show_parent = blocks.BooleanBlock(
        default=False, required=False, help_text=_("Include the parent page as a menu item")
    )

    title = blocks.CharBlock(
        required=False, max_length=100, help_text=_("Optional title to display instead of the parent page title")
    )

    def get_context(self, value, parent_context=None):
        """Add the page children to the template context."""
        context = super().get_context(value, parent_context)

        if value.get("parent_page"):
            parent_page = value["parent_page"]
            max_levels = value.get("max_levels", 1)
            show_parent = value.get("show_parent", False)

            # Get child pages with optimized query strategy
            if max_levels == 1:
                # For single level, use simple optimized query
                child_pages = self._get_child_pages_single_level(parent_page)
            else:
                # For multiple levels, use recursive method
                child_pages = self._get_child_pages(parent_page, max_levels)

            context.update(
                {
                    "child_pages": child_pages,
                    "parent_page": parent_page if show_parent else None,
                    "display_title": value.get("title_override") or (parent_page.title if show_parent else None),
                }
            )

        return context

    def _get_child_pages_single_level(self, parent_page):
        """Optimized method for getting single-level child pages."""
        children = (
            parent_page.get_children()
            .live()
            .in_menu()
            .select_related('content_type')  # Avoid N+1 queries for content_type
            .specific()
        )
        
        return [{"page": child, "children": []} for child in children]

    def _get_child_pages(self, parent_page, max_levels, current_level=1):
        """Recursively get child pages up to max_levels with query optimization."""
        if current_level > max_levels:
            return []

        # Optimize queries with select_related for content_type field
        children = (
            parent_page.get_children()
            .live()
            .in_menu()
            .select_related('content_type')  # Avoid N+1 queries for content_type
            .specific()
        )
        
        result = []

        for child in children:
            child_data = {
                "page": child,
                "children": self._get_child_pages(child, max_levels, current_level + 1)
                if current_level < max_levels
                else [],
            }
            result.append(child_data)

        return result

    class Meta:
        icon = "heroicons-rectangle-group-outline"
        label = _("Children Page Links")
        template = "wagtail_feathers/blocks/auto_page_links_block.html"
        value_class = LinkStructValue
        preview_value = {
            "parent_page": None,  # Will be handled in preview
            "max_levels": 2,
            "show_parent": True,
            "title_override": _("Sample Menu Section"),
        }
        description = _("Automatically generate menu items from page children")


class SubMenuDividerBlock(blocks.StructBlock):
    """A visual divider for separating menu sections."""

    label = blocks.CharBlock(required=False, max_length=50, help_text=_("Optional label for the divider section"))

    class Meta:
        icon = "horizontalrule"
        label = _("Menu Divider")
        template = "wagtail_feathers/blocks/submenu_divider_block.html"
        preview_value = {"label": _("Menu Section")}
        description = _("A visual separator between menu items")


""" Recursive Menu Block
"""
class RecursiveMenuBlock(blocks.StructBlock):
    """Navigation link block with nested children support using local_blocks."""

    def __init__(self, local_blocks=(), max_depth=3, _depth=0, *args, **kwargs):
        _depth += 1

        if _depth <= max_depth:
            base_blocks = (
                (
                    ("submenu", RecursiveMenuBlock(local_blocks, max_depth, _depth, *args, **kwargs)),
                    ("autofill_submenu", PageMenuBlock()),
                )
                if _depth < max_depth
                else ()
            )

            base_blocks += (
                ("internal_link", InternalLinkBlock()),
                ("external_link", ExternalLinkBlock()),
                ("divider", SubMenuDividerBlock()),
            )

            local_blocks += (
                ("title", blocks.CharBlock(max_length=100, label=_("Submenu Display Title"))),
                ("menu_items", blocks.StreamBlock(base_blocks)),
                *local_blocks,
            )
        super().__init__(local_blocks, _depth=_depth, **kwargs)

    class Meta:
        icon = "heroicons-queue-list-outline"
        label = _("Submenu")
        template = "wagtail_feathers/blocks/_nested_navigation_link_block.html"
        form_classname = "struct-block submenu-block"
        label_format = label + ": {title}"


""" StreamBlocks
https://docs.wagtail.org/en/stable/topics/streamfield.html#streamblock
StreamBlock defines a set of child block types that can be mixed and repeated in any sequence, 
via the same mechanism as StreamField itself.  StreamBlock can also be subclassed in the same way 
as StructBlock, with the child blocks being specified as attributes on the class.  Then, it can 
also be passed to a StreamField definition, instead of passing a list of block types
"""


# CommonContentBlock will be defined after all individual blocks


class LinkStreamBlock(blocks.StreamBlock):
    """StreamBlock that allows editors to add a single link of type internal or external."""

    internal = InternalLinkBlock()
    external = ExternalLinkBlock()

    class Meta:
        icon = "link"
        label = "Link"
        # min_num = 1
        # max_num = 1


class MenuStreamBlock(blocks.StreamBlock):
    """StreamBlock that allows editors to add menu items."""

    submenu = RecursiveMenuBlock()
    internal = InternalLinkBlock()
    external = ExternalLinkBlock()
    page_links = PageMenuBlock()

    class Meta:
        icon = "heroicons-queue-list-outline"
        label = _("Menu Items")
        help_text = _("Add menu items to the navigation bar.")


class FooterMenuStreamBlock(blocks.StreamBlock):
    """StreamBlock that allows editors to either add links or children from a page's children."""

    page_links = PageMenuBlock()
    internal = InternalLinkBlock()
    external = ExternalLinkBlock()

    class Meta:
        icon = "heroicons-queue-list-outline"
        label = _("Menu Items")
        help_text = _("Each section will be a column in the footer.")


class HeroContentBlock(blocks.StreamBlock):
    """A StreamBlock specifically for hero sections and page headers."""

    hero = HeroBlock(label="Hero Section")
    
    class Meta:
        icon = "heroicons-photo-outline"
        label = _("Hero Content")
        help_text = _("Add hero sections for page headers and landing areas.")
        min_num = 0
        max_num = 1  


class PageHeaderBlock(blocks.StreamBlock):
    """A StreamBlock for page headers including hero and intro sections."""

    heading = PageHeadingBlock(label="Heading", required=False)
    image = HeaderImageBlock(label="Image", required=False)
    hero = HeroBlock(label="Hero Section", required=False)
    cta = CallToActionBlock(label="Call to Action", required=False)

    class Meta:
        icon = "heroicons-rectangle-stack-outline"
        label = _("Page Header")
        help_text = _("Page headers blocks: hero, cta, image, heading, sub_heading.")
        min_num = 0
        max_num = 5


class FAQItemBlock(BaseBlock):
    """A single FAQ question and answer block."""
    
    component_type = "faq_item"
    default_variant = "default"

    question = blocks.CharBlock(
        max_length=200,
        help_text=_("The FAQ question")
    )
    
    answer = blocks.RichTextBlock(
        features=["bold", "italic", "link", "ul", "ol"],
        help_text=_("The answer to the question")
    )
    
    class Meta:
        icon = "help"
        template = "wagtail_feathers/blocks/faq_item_block.html"
        label = _("FAQ Item")
        preview_value = {
            "question": _("How do I get started?"),
            "answer": _("Getting started is easy! Simply follow our step-by-step guide to begin your journey.")
        }
        description = _("A single FAQ question and answer")


class FAQSectionBlock(BaseBlock):
    """A section of related FAQ items with an optional heading."""
    
    component_type = "faq_section"
    default_variant = "default"

    section_title = blocks.CharBlock(
        max_length=100,
        required=False,
        help_text=_("Optional section heading")
    )
    
    faqs = blocks.StreamBlock([
        ("faq", FAQItemBlock()),
    ], min_num=1)
    
    class Meta:
        icon = "list-ul"
        template = "wagtail_feathers/blocks/faq_section_block.html"
        label = _("FAQ Section")
        preview_value = {
            "section_title": _("Getting Started"),
            "faqs": []
        }
        description = _("A group of related FAQ items with optional section heading")


class FAQSectionEmbedBlock(BaseBlock):
    """Embed FAQ items from a specific category anywhere in content."""
    
    component_type = "faq_embed"
    default_variant = "default"

    section_title = blocks.CharBlock(
        max_length=100,
        required=False,
        help_text=_("Optional title for this FAQ section")
    )
    
    faq_category = blocks.ChoiceBlock(
        choices=[],  # Will be populated dynamically
        help_text=_("Select FAQ category to display")
    )
    
    max_items = blocks.IntegerBlock(
        default=5,
        min_value=1,
        max_value=20,
        help_text=_("Maximum number of FAQ items to show")
    )
    
    show_view_all_link = blocks.BooleanBlock(
        default=True,
        required=False,
        help_text=_("Show 'View All FAQs' link")
    )
    
    faq_page = blocks.PageChooserBlock(
        required=False,
        help_text=_("Link to full FAQ page (for 'View All' link)")
    )

    def get_form_context(self, value, prefix='', errors=None):
        """Update category choices when form is rendered."""
        context = super().get_form_context(value, prefix, errors)
        
        # Only update choices when form is actually being rendered (not during startup)
        # TODO: Verify if there is another way to achieve this
        try:
            from django.apps import apps
            if not apps.ready:
                return context
                
            from wagtail_feathers.models.faq import FAQCategory
            categories = FAQCategory.objects.all()
            choices = [(str(cat.id), cat.name) for cat in categories]
            if not choices:
                choices = [('', _('No FAQ categories available'))]
            
            # Update the field choices
            if hasattr(self.child_blocks['faq_category'], 'field'):
                self.child_blocks['faq_category'].field.choices = choices
            elif hasattr(self.child_blocks['faq_category'], 'choices'):
                self.child_blocks['faq_category'].choices = choices
                
        except Exception:
            # Fallback if models aren't ready yet
            choices = [('', _('No categories available'))]
            if hasattr(self.child_blocks['faq_category'], 'field'):
                self.child_blocks['faq_category'].field.choices = choices
            elif hasattr(self.child_blocks['faq_category'], 'choices'):
                self.child_blocks['faq_category'].choices = choices
        
        return context
    
    def clean(self, value):
        """Validate the selected FAQ page is actually an FAQ page."""
        cleaned_data = super().clean(value)
        
        # Validate that faq_page is actually an FAQBasePage instance
        faq_page = cleaned_data.get('faq_page')
        if faq_page:
            try:
                from wagtail_feathers.models.specialized_pages import FAQBasePage
                if not isinstance(faq_page.specific, FAQBasePage):
                    raise blocks.StructBlockValidationError({
                        'faq_page': blocks.ErrorList([_('Please select an FAQ page.')])
                    })
            except ImportError:
                # If models aren't available, skip validation
                pass
        
        return cleaned_data

    def get_context(self, value, parent_context=None):
        """Add FAQ items to template context."""
        context = super().get_context(value, parent_context)
        
        try:
            from wagtail_feathers.models.faq import FAQ, FAQCategory
            
            category_id = value.get('faq_category')
            max_items = value.get('max_items', 5)
            
            if category_id:
                faqs = FAQ.objects.filter(
                    category_id=category_id,
                    live=True
                ).order_by('sort_order')[:max_items]
                
                category = FAQCategory.objects.filter(id=category_id).first()
                
                context.update({
                    'faqs': faqs,
                    'category': category,
                    'faq_page_url': value.get('faq_page').url if value.get('faq_page') else None,
                })
        except Exception:
            context.update({
                'faqs': [],
                'category': None,
                'faq_page_url': None,
            })
        
        return context
    
    class Meta:
        icon = "help"
        template = "wagtail_feathers/blocks/faq_section_embed_block.html"
        label = _("FAQ Section")
        preview_value = {
            "section_title": _("Frequently Asked Questions"),
            "faq_category": "",
            "max_items": 5,
            "show_view_all_link": True,
        }
        description = _("Embed FAQ items from a category anywhere in your content")


class BaseSectionBlock(BaseBlock):
    """Base class for section blocks with heading and screen reader support.
    
    Provides a lightweight alternative to BaseContainerBlock for simple,
    predictable content sections. Inherits theme variant support from BaseBlock.
    """
    
    component_type = "section"
    default_variant = "default"
    
    fluid = blocks.BooleanBlock(
        required=False,
        default=False,
        label=_("Full width"),
        help_text=_("If checked, the section will span the full width of the page without container padding."),
    )
    heading = blocks.CharBlock(
        form_classname="title",
        icon="title",
        required=True,
        help_text=_("Section heading (will use H2 in templates)")
    )
    sr_only_label = blocks.BooleanBlock(
        required=False,
        label=_("Screen reader only label"),
        help_text=_("If checked, the heading will be hidden from view and available to screen-readers only."),
    )

    class Meta:
        abstract = True
        icon = "title"


class BaseCardSectionBlock(BaseSectionBlock):
    """Base class for card-based sections.
    
    Extends BaseSectionBlock to include a list of cards with sensible defaults
    for typical card grid sections.
    """
    
    component_type = "cards-section"
    default_variant = "default"
    
    cards = blocks.ListBlock(
        CardBlock(),
        max_num=9,
        label=_("Cards"),
        help_text=_("Add cards to display in this section (max 9 to avoid performances issues)")
    )
    
    class Meta:
        abstract = True
        icon = "form"


class CardSectionBlock(BaseCardSectionBlock):
    """A complete card section implementation.
    
    Ready-to-use card section that displays a heading and grid of cards.
    Supports theme variants and responsive layout.
    """
    
    class Meta:
        template = "wagtail_feathers/blocks/card_section_block.html"
        icon = "form"
        label = _("Card Section")
        help_text = _("A section with heading and grid of cards")


class CommonContentBlock(blocks.StreamBlock):
    """A streamBlock that gathers typical blocks for page content (excluding hero sections)."""

    heading_block = HeadingBlock(label="Heading")
    paragraph_block = blocks.RichTextBlock(
        label="Paragraph",
        icon="pilcrow",
        template="wagtail_feathers/blocks/paragraph_block.html",
        features=["h2", "h3", "h4", "bold", "italic", "link", "ul", "ol", "superscript", "subscript"],
        preview_value=(
            """
            <h2>Our scientific commitment</h2>
            <p>In the realm of science, <b>discovery</b> has <i>always</i> been our driving force.
            <a href="https://en.wikipedia.org/wiki/Scientific_method">Scientific methods</a>
            are crucial for progress, and – research is the most rewarding of all.
            We take pride in transforming hypotheses and experiments into groundbreaking
            findings with precision and rigor.</p>
            """
        ),
        description="A rich text paragraph",
    )
    markdown_block = MarkdownBlock(icon="code", label="Markdown")
    image_block = ImageBlock(label="Image")
    image_grid = ImageGridBlock(label="Image Grid")
    image_collection_gallery = ImageCollectionGalleryBlock(label="Image Collection")
    block_quote = QuoteBlock(label="Quote")
    embed_block = EmbedBlock(
        label="Embed Block",
        help_text="Insert an embed URL e.g https://www.youtube.com/watch?v=SGJFWirQ3ks",
        icon="media",
        template="wagtail_feathers/blocks/embed_block.html",
        preview_template="wagtail_feathers/preview/static_embed_block.html",
        preview_value="https://www.youtube.com/watch?v=mwrGSfiB1Mg",
        description=_("An embedded video or other media"),
    )
    cta_block = CallToActionBlock(label="Call to Action")
    card_block = CardBlock(label="Card")
    card_section = CardSectionBlock(label="Card Section")
    faq_section = FAQSectionEmbedBlock(label="FAQ Section")
    table_block = TableBlock(label="Table")
