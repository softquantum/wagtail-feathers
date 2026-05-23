# Changelog

## v1.0.0rc6

### Bug Fixes

- **`BaseBlock` theme-panel ordering**: editors saw the Theme settings panel at the *end* of every `BaseBlock` StructBlock (e.g. just before children on `CardsContainerBlock`, at the very bottom on leaf blocks with only class-declared fields). Root cause was upstream in Wagtail's own `BaseStructBlock.__init__` (`wagtail/blocks/struct_block.py:253`): it snapshots `self.meta.form_layout = self.get_form_layout()` *before* the previous `BaseBlock.__init__` did its `OrderedDict` reorder of `self.child_blocks`. The snapshot used the pre-reorder order, the Telepath admin adapter reads `form_layout`, so the runtime reorder was invisible to the form. Replaced the runtime reorder with a `get_form_layout()` override that returns `BlockGroup([theme, …content…, nested BlockGroup(template_variant)])` — a single source of truth using Wagtail's documented `form_layout` API. No data migration is required; existing saved StructValues are unaffected.

### Improvements

- **Block-level `template_variant`**: any `BaseBlock` subclass whose `Meta.template` has on-disk variant siblings now exposes a `template_variant` field, rendered inside a collapsed **Template variant** panel at the bottom of the admin form. Choices are discovered from disk by scanning the active theme(s) for `<base_template>--*.html` siblings of the block's `Meta.template`; if no siblings exist, the field is **not** injected at all (so blocks without variants stay clean — no empty single-choice dropdown). When a variant is selected, `Block.get_template()` returns `[<base>--<variant>.html, <base>.html]` so Django's template loader tries the variant first and silently falls back to the default if the variant file isn't on disk. Mirrors the existing page-level `template_variant` pattern (`models/specialized_pages.py:73,108-125,147`) — same naming convention (`<basename>--<variant>.html`), same fallback semantics. **Decoupled from `theme.theme_variant`**: theme variants remain cosmetic-styling concerns keyed off `theme.json`; template variants are structural/DOM concerns keyed off filenames. Two orthogonal axes, two independent dropdowns. Implementation note: the panel is a nested `BlockGroup` in the layout's `children` (not the top-level `settings=`), because Wagtail's admin JS only renders a visible toggle for the settings group when the parent StructBlock is wrapped in a `<section data-panel>` — which doesn't happen for non-collapsible StructBlocks inside a StreamField.
- **New `TemplateVariantChooserBlock` class** — public, importable from `wagtail_feathers.blocks`. Auto-instantiated by `BaseBlock` but can also be added manually to any `StructBlock`. Disk discovery is exposed as the public `TemplateVariantChooserBlock.discover_variants(base_template)` static method so callers can probe variants outside the block constructor.

### Downstream migration note

`makemigrations` will detect a `block_lookup` shape change on every model whose StreamFields reference a `BaseBlock` subclass (because `template_variant` is now a new child of `BaseBlock`). One-time noisy migration per downstream project; no DB column changes — it's a StreamField field-order snapshot.

## v1.0.0rc5

### Improvements

- **`ImageBlock`**: added a `fit` field (`cover` / `contain`, default `cover`). The default keeps the existing editorial behaviour — images are server-side cropped via `fill-…` and rendered into a 16:9 frame with `aspect-video object-cover`. Selecting **Contain — fit without cropping** switches the block to a `max-…` render with `block mx-auto h-auto max-w-full max-h-[640px] w-auto`, preserving the natural aspect ratio. Use this for logos, diagrams, or any image where cropping would lose meaning. The field is a StreamField sub-block addition, so no Django migration is required; existing `image_block` entries deserialize with `fit="cover"` and render identically to before. Projects that override `wagtail_feathers/blocks/image_block.html` should branch on `self.fit` to pick between cover and contain rendering.

## v1.0.0rc4

### Improvements

- **`CardBlock`**: added an optional `icon` field that stores a Heroicon slug (e.g. `"shield-check-solid"`). When set, downstream templates can render it via `{% svg_icon name="heroicons-{{ value.icon }}" %}` above the heading instead of using the `image` field. Existing `CardBlock` instances are unaffected (the field is optional). Projects that override `card_block.html` should branch on `value.icon` to pick between icon-style and image-style cards.
- **`{% breadcrumbs %}` templatetag** (`navigation_tags`): added a `min_depth` parameter (default `2`, preserves prior behavior of hiding the trail on the home page only). Set `{% breadcrumbs min_depth=3 %}` to also suppress the redundant `Home / Section` trail on direct children of home — useful for themes that consider single-step breadcrumbs visual noise. The condition is `self.depth <= min_depth`, using Wagtail's tree-depth convention (root=1, home=2, top-level sections=3, …).

### Bug Fixes

- **`CardsContainerBlock`**: fixed a structural bug where the block's `content` StreamBlock accepted `heading` and `columns` sub-blocks instead of `CardBlock` instances, making it impossible to actually add cards to a card grid. The buggy subclass `__init__` was passing config fields (`heading`, `columns`) through `local_blocks`, which `BaseContainerBlock` then incorrectly wrapped into the `content` StreamBlock — also masking the class's own `content_streamblocks = [("card", CardBlock())]` declaration. The `__init__` override has been removed; `heading` (now optional, overriding the inherited required=True) and `columns` are declared as struct-level fields, and `BaseContainerBlock` correctly assembles the `content` StreamBlock from `content_streamblocks`. The fix preserves caller-side extensibility (`CardsContainerBlock(local_blocks=[("featured", FeaturedCardBlock())])` still works to substitute a custom card type).
- **`cards_container_block.html` template**: removed dead first half that referenced the non-existent `value.cards` attribute. The template now renders only `value.content` (the cards StreamBlock) under a `.cards-container` / `.cards-grid` wrapper.

## v1.0.0rc3

### Breaking

- Bumped minimum Python to **3.12**, Wagtail to **7.4 LTS**, and Django to **5.2** (Django 6.x supported). Python 3.11 and Wagtail 6.x are no longer supported. Test matrix runs on Python 3.12 / 3.13 / 3.14.

### Improvements

- Per-site theming now resolves correctly at the template loader and static finder layer. New `wagtail_feathers.middleware.theme_site_middleware` (sync + async) binds the current request's Wagtail `Site` to a `contextvars.ContextVar` so themes resolve per-request. Public helpers `get_current_site`, `set_current_site`, and `use_site` are available from `wagtail_feathers.themes` for management commands, scripts, and tests. **Action required:** add `wagtail_feathers.middleware.theme_site_middleware` to `MIDDLEWARE`.
- `get_active_theme_info()` now accepts a `site` argument and is cached in Django's default cache (per-site key) instead of a process-wide `lru_cache`. Cache is invalidated automatically when `SiteSettings.active_theme` changes.
- New `wagtail_feathers.themes.ThemeAwareCachedLoader`: drop-in subclass of Django's `cached.Loader` that keys cache entries by `(site_id, template_name)`. Use it in place of `cached.Loader` if you wrap our template loader, otherwise stock caching would serve one site's theme template to another.
- Admin template-variant discovery (`FeatherBasePage.get_available_template_variants`, `FormBasePage.get_available_template_variants`) now unions variants across every installed theme via the new `ThemeRegistry.get_all_theme_template_dirs()`, so the editor exposes variants from all sites' themes, not just the default site's.

### Bug Fixes

- Fixed silent multi-site theming bug: `TemplateLoader.get_dirs()` and `ThemeAwareFileSystemFinder.get_theme_locations()` always resolved through the default site regardless of which site the request belonged to. They now read the current site from the new context variable populated by `theme_site_middleware`.

## v1.0.0rc2

### Improvements

- Rewrote viewsets `__init__.py` with lazy `__getattr__` pattern
- Refactored viewsets with `LocaleAwareMixin`
- Use `LocaleColumn` instead of `'locale'` in viewsets
- wagtail-localize now auto-discovers the FAQ `ChooserBlock` as a FK to a `TranslatableMixin` model
- Reading time feature now uses language-specific reading speeds to align with wagtail admin content metrics

### Bug Fixes

- Fixed navigation unique constraint to be localized
- Navigation slugs are now synchronized fields with wagtail-localize
- `FormBasePage` slug is now a sync field with wagtail-localize

### Internal

- Refactored test suite
- Updated theme integration tests
- Updated and added new migration files
