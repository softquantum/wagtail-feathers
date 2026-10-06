# Wagtail Feathers Demo Site

This demo site showcases the features and capabilities of the wagtail-feathers package. It runs on any Wagtail version supported by the package (7.3+ and 8.x) with Wagtail's default `Page` model.

## Quick Start

Run all commands from the `demo/` directory.

1. **Install dependencies** (installs wagtail-feathers in editable mode from the parent directory):

   ```bash
   uv pip install -r requirements.txt
   # or
   pip install -r requirements.txt
   ```

2. **Create the database and load the demo data:**

   ```bash
   python manage.py migrate
   python manage.py setup_demo_data
   ```

3. **Start the server:**

   ```bash
   python manage.py runserver
   ```

4. **Access the demo:**
   - **Frontend:** http://localhost:8000
   - **Admin:** http://localhost:8000/admin
   - **Login:** `admin` / `admin123` (created by `setup_demo_data` when no superuser exists)

## Demo Data

`setup_demo_data` can be run repeatedly: it deletes the existing demo page tree and recreates it. It creates:

- **Home Page** (`HomePage`), set as the root page of the default site
- **About** (`WebPage`)
- **Blog** (`ArticleIndexPage`) with three sample **articles** (`ArticlePage`)
- **Taxonomy:** a *Technology > Wagtail* category tree, and two classifier groups (*Topics* as subjects, *Level* as attributes) assigned to the articles
- A superuser, if none exists

Wagtail's default "Welcome" page is removed so the demo home page can use the `home` slug.

## Features Demonstrated

### Page models (`showcase/models.py`)
- **`HomePage`, `WebPage`** built on `WebBasePage` (page header blocks and common content blocks)
- **`ArticleIndexPage`** built on `IndexPage`
- **`ArticlePage`** built on `ItemPage` (publication dates, authorship, taxonomy)
- **`AuthorPage`, `FAQPage`** built on `WebBasePage`
- **`ContactPage`** built on `FormBasePage`, with its `ContactFormField`

### Package features
- **Theme system:** the `quantum` theme in `themes/`, activated with `WAGTAIL_FEATHERS_ACTIVE_THEME` in `settings.py`
- **Template variants:** `--<variant>.html` page templates in `themes/quantum/templates/pages/`
- **SEO:** meta tags, Open Graph, Twitter Cards and structured data
- **Taxonomy:** categories and classifiers, managed under *Settings > Wagtail Feathers* in the admin
- **Navigation, people, FAQ and geographic snippets**

## Development Workflow

The demo uses an editable installation of wagtail-feathers (`-e ../`), so changes to the package in `../src/wagtail_feathers/` are reflected immediately. Restart the server after adding template variants, since block variants are discovered at startup.

## Project Structure

```
demo/
├── settings.py            # Django project settings
├── urls.py                # URL configuration
├── wsgi.py                # WSGI application
├── manage.py              # Django management script
├── showcase/              # Demo application showcasing wagtail-feathers
│   ├── models.py          # Example page models using wagtail-feathers
│   ├── viewsets.py        # Example admin viewsets
│   ├── wagtail_hooks.py   # Example Wagtail hooks
│   ├── management/        # Management commands (setup_demo_data)
│   └── migrations/        # Database migrations
├── themes/                # Demo themes (quantum)
├── media/                 # User uploads
├── requirements.txt       # Demo dependencies
└── README.md              # This file
```

## Database Reset

```bash
rm db.sqlite3
python manage.py migrate
python manage.py setup_demo_data
```

## Next Steps

- Explore the admin interface to see wagtail-feathers panels and functionality
- Check the sample articles to see SEO and taxonomy features in action
- Modify `showcase/models.py` to test your own wagtail-feathers features
- Use this demo as a reference for implementing wagtail-feathers in your own projects
