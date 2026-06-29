# Floor Plan Compliance - Django

This is a Django template-based conversion of the original `floorplan-compliance` React + Vite application.

## What was converted

- **Authentication**: Login/logout using Django sessions (replaces Supabase Auth).
- **Users**: User list and user management with roles (Admin, Reviewer, User).
- **Projects**: CRUD for projects.
- **Floor Plans**: Upload, list, delete, and view floor plans. PDFs and images are converted to PNG automatically and displayed as images.
- **Dashboard**: Project, floor plan, and user counts.
- **Tabs on project details**: Overview, Floor Plans, Reviews (placeholder), Compliance (placeholder).

## What is not included

The original React app contained specialized frontend libraries (Fabric.js, Tesseract.js, DXF parser, Three.js, MUI Data Grid). These were not fully re-implemented in Django templates because they are inherently client-side features. DXF/DWG files can be downloaded but are not converted to PNG.

## Requirements

- Python 3.10+
- Django 6.0
- Pillow
- PyMuPDF

## Setup

```powershell
# 1. Create/activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Seed demo data (optional)
python manage.py seed_data

# 5. Start the development server
python manage.py runserver
```

## Demo login

- **Email**: `admin@example.com`
- **Password**: `admin123`

## Management commands

- `python manage.py seed_data` - Create demo admin and sample projects.
- `python manage.py convert_existing_floorplans` - Convert previously uploaded PDFs/images to PNG.

## Project layout

- `floorplan_compliance/` - Django project settings and URLs.
- `core/` - Main application with models, views, forms, templates, and static files.
- `media/floor_plans/` - Uploaded floor plan files.
- `media/floor_plans/converted/` - Auto-generated PNG conversions.
