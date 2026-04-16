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
- Django 6.x
- Pillow
- MySQL Server 8.x (or compatible)
- PyMySQL
- cryptography

## Setup

1. Create and activate a virtual environment.
2. Install the dependencies from `requirements.txt`.
3. Make sure MySQL server is running.
4. Create the database in MySQL:

	```sql
	CREATE DATABASE hospital_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
	```

5. Update database credentials in `hospital/settings.py` with your own local MySQL account.
6. Run migrations with `python manage.py migrate`.
7. Start the development server with `python manage.py runserver`.

## MySQL Database Configuration

Current MySQL settings in `hospital/settings.py`:

- ENGINE: `django.db.backends.mysql`
- NAME: `hospital_db`
- USER: `root`
- PASSWORD: `1234`
- HOST: `127.0.0.1`
- PORT: `3306`

If your local MySQL credentials are different, update these values in `hospital/settings.py` before running migrations.

## Team Member Setup (Recommended)

For other team members, do not share one root password across all machines. Each member should use their own local MySQL user and password.

Suggested personal setup values:

- NAME: `hospital_db`
- USER: your own MySQL username (example: `hospital_user`)
- PASSWORD: your own MySQL password
- HOST: `127.0.0.1`
- PORT: `3306`

Then use those values in the `DATABASES` section of `hospital/settings.py`.

## Optional MySQL User Setup

You can create a dedicated MySQL user instead of using root:

```sql
CREATE USER 'hospital_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON hospital_db.* TO 'hospital_user'@'localhost';
FLUSH PRIVILEGES;
```

## Project Notes

- MySQL is used as the local development database.
- `media/` stores uploaded profile images and other user files.
- `static/` contains the project assets.

