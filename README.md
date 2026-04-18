# Smart Hospital Manager

A Django-based hospital management platform focused on clean role-based workflows for doctors and patients.

## Project Highlights

- Role-based authentication for Doctor and Patient users
- Dedicated dashboards for each role
- Editable profile page with image upload
- Recovery question based password reset flow
- Random demo data generator for fast local testing

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Django 6 |
| Database | MySQL 8 |
| Image Handling | Pillow |
| MySQL Driver | PyMySQL |

## Quick Start

For most users, this is enough:

```bash
git clone https://github.com/your-username/your-repo.git
cd SmartHospitalManager
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_users --doctors 10 --patients 10 --password Pass@123
python manage.py runserver
```

Open: http://127.0.0.1:8000/

## New Device Setup (Windows)

### 1) Install MySQL Server

Choose one:

```bash
winget install Oracle.MySQL
```

```bash
choco install mysql
```

Or install from the official MySQL Installer Community package.

Verify installation:

```bash
mysql --version
```

### 2) Start MySQL Service

```bash
net start MySQL80
```

### 3) Create Project Database

Login with default project credentials:

```bash
mysql -u root -p1234 -h 127.0.0.1 -P 3306
```

Then run:

```sql
CREATE DATABASE hospital_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4) Install Python Dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

For Git Bash activation:

```bash
source .venv/Scripts/activate
```

### 5) Apply Migrations, Seed, and Run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_users --doctors 10 --patients 10 --password Pass@123
python manage.py runserver
```

## MySQL Credentials (Current Project)

| Key | Value |
| --- | --- |
| Username | root |
| Password | 1234 |
| Host | 127.0.0.1 |
| Port | 3306 |
| Database name | hospital_db |

If your machine uses different credentials, update the DATABASES values in hospital/settings.py.

## Seed Demo Data

Generate random users for testing:

```bash
python manage.py seed_users
```

Custom counts:

```bash
python manage.py seed_users --doctors 10 --patients 10 --password Pass@123
```

## Migration Guide

- Use `python manage.py makemigrations` only when model files change.
- For command-only changes (example: users/management/commands/seed_users.py), `makemigrations` is not required.

## Optional Team-Friendly MySQL User

Instead of sharing root, create a dedicated user per machine:

```sql
CREATE USER 'hospital_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON hospital_db.* TO 'hospital_user'@'localhost';
FLUSH PRIVILEGES;
```

Then update USER and PASSWORD in hospital/settings.py.

## Project Notes

- MySQL is used for local development.
- media/ stores uploaded profile images.
- static/ contains static assets.

