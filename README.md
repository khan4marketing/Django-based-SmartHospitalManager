# Hospital Management

A Django-based hospital management project with user registration, login, role-based dashboards, and profile management for doctors and patients.

## Features

- User registration and login
- Doctor and patient roles
- Profile editing
- Separate dashboards for doctors and patients
- Blog-related models and app structure are still present in the codebase for future expansion

## Requirements

- Python 3.11+ recommended
- Django
- Pillow

## Setup

1. Create and activate a virtual environment.
2. Install the dependencies from `requirements.txt`.
3. Run migrations with `python manage.py migrate`.
4. Start the development server with `python manage.py runserver`.

## Project Notes

- `db.sqlite3` is the local development database.
- `media/` stores uploaded profile images and other user files.
- `static/` contains the project assets.

