# Wagtail Feathers Demo Site

This demo site showcases the features and capabilities of the wagtail-feathers package.

## Quick Start

1. **Install dependencies:**
   
   **Option A: Using uv (recommended)**
   ```bash
   uv pip install -r requirements.txt
   ```
   
   **Option B: Using pip**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup note:**
   Currently, the wagtail-feathers package has migration dependencies on the parent softquantum project. For standalone demo usage:
   
   **Option A: Use parent project database**
   ```bash
   # From wagtail-feathers root directory
   cd ../
   python manage.py migrate
   python wagtail_feathers/demo/manage.py setup_demo_data
   python wagtail_feathers/demo/manage.py runserver
   ```
   
   **Option B: Simplified demo (recommended for development)**
   ```bash
   python manage.py check  # Verify configuration
   # Note: migrations will fail due to media app dependency
   # This is expected and will be resolved when package is extracted
   ```

3. **Access the demo:**
   - **Frontend:** http://localhost:8000
   - **Admin:** http://localhost:8000/admin
   - **Login:** `admin` / `admin123`

## Features Demonstrated

### Core Features
- **FeatherBasePage:** Base page model with common functionality
- **SEO Optimization:** Meta tags, Open Graph, Twitter Cards
- **Reading Time:** Automatic reading time calculation
- **Theme System:** Flexible theming capabilities

### Demo Content
- **Home Page:** Introduction to wagtail-feathers
- **Article Index:** Article listing with wagtail-feathers features  
- **Sample Articles:** Showcase SEO and reading time features

## Development Workflow

This demo uses an editable installation of wagtail-feathers (`-e ../`), which means:

- **Live Updates:** Changes to the wagtail-feathers package are immediately reflected
- **Local Development:** Perfect for testing features while developing the package
- **Real-time Testing:** See how your package changes affect a real Wagtail site

## Project Structure

```
demo/
├── settings.py            # Django project settings
├── urls.py               # URL configuration  
├── wsgi.py               # WSGI application
├── manage.py             # Django management script
├── showcase/             # Demo application showcasing wagtail-feathers
│   ├── models.py         # Example page models using wagtail-feathers
│   ├── management/       # Management commands
│   └── migrations/       # Database migrations
├── static/              # Demo static files
├── media/               # User uploads
├── requirements.txt     # Demo dependencies
└── README.md            # This file

```

## Customization

### Adding New Features
1. Modify the wagtail-feathers package in `../src/wagtail_feathers/`
2. Update demo models in `showcase/models.py` to showcase new features
3. Test changes by running the demo server

### Database Reset
To reset the demo data:
```bash
rm db.sqlite3
python manage.py migrate
python manage.py setup_demo_data
```

## Package Extraction Notes

When extracting wagtail-feathers as a standalone package:

1. **Migration Dependencies:** Remove references to `('media', '0001_initial')` from package migrations
2. **Demo Independence:** This demo structure is ready for standalone operation once migrations are cleaned up
3. **Testing:** Use this demo to verify package functionality works independently of the parent project

## Tips for Package Development

1. **Use the Demo:** Always test package changes using this demo site
2. **Sample Data:** The `setup_demo_data` command creates realistic test content
3. **Admin Interface:** Use `/admin` to see how your package integrates with Wagtail's admin
4. **Templates:** Add demo templates to showcase your package's frontend capabilities

## Next Steps

- Explore the admin interface to see wagtail-feathers panels and functionality
- Check the sample articles to see SEO and reading time features in action
- Modify `showcase/models.py` to test your own wagtail-feathers features
- Use this demo as a reference for implementing wagtail-feathers in your own projects