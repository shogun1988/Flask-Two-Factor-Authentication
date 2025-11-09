# Flask Two-Factor Authentication (TOTP)

A minimal Flask app that demonstrates user registration, login, and Time-based One-Time Password (TOTP) two‑factor authentication (2FA) using PyOTP and Google Authenticator.

Original tutorial: https://www.freecodecamp.org/news/how-to-implement-two-factor-authentication-in-your-flask-app/

## Features
- User registration and login with hashed passwords (Flask‑Bcrypt)
- TOTP 2FA setup with QR code (PyOTP + qrcode + Pillow)
- 2FA verification on login (Flask‑Login)
- Flask‑SQLAlchemy ORM and Flask‑Migrate migrations

## Tech stack
- Python 3.10+
- Flask, Flask‑Login, Flask‑Bcrypt, Flask‑WTF, Flask‑SQLAlchemy, Flask‑Migrate
- PyOTP, qrcode, Pillow
- python‑decouple for configuration

---

## Prerequisites
- Windows PowerShell (pwsh)
- Python 3.x installed and on PATH

> Tip: Use a virtual environment to keep dependencies isolated.

---

## Installation (Windows PowerShell)

1) Clone and enter the project folder
```powershell
# If you haven't already cloned it, do so, then cd into it
# git clone <this-repo-url>
cd D:\freecodecamp\Flask-Two-Factor-Authentication
```

2) Create and activate a virtual environment
```powershell
python -m venv .\venv
.\venv\Scripts\Activate.ps1
```

3) Install dependencies
```powershell
pip install -r requirements.txt
```

4) Configure environment variables
- Copy `.env.example` to `.env` and adjust values as needed.

Example `.env`:
```
APP_SETTINGS=config.DevelopmentConfig
DATABASE_URL=sqlite:///dev.sqlite
SECRET_KEY=change-me
APP_NAME=Flask2FA
```

Notes:
- `APP_SETTINGS` controls which config class to use. If not set, it defaults to `config.DevelopmentConfig`.
- `DATABASE_URL` defaults to `sqlite:///dev.sqlite` if not set.
- Use a strong, random `SECRET_KEY` in any non‑dev environment.

5) Initialize the database (first run only)
```powershell
.\venv\Scripts\python.exe .\manage.py db init
.\venv\Scripts\python.exe .\manage.py db migrate -m "initial"
.\venv\Scripts\python.exe .\manage.py db upgrade
```

6) Run the app
```powershell
.\venv\Scripts\python.exe .\manage.py run
```
Then open http://127.0.0.1:5000/ in your browser.

---

## How to use
1) Register a user
   - Go to `/register`, create a username and password.
2) Set up 2FA
   - You will be redirected to `/setup-2fa`.
   - Scan the QR code with an authenticator app (Google Authenticator, Microsoft Authenticator, etc.).
   - The QR encodes `otpauth://` with your username and the app name from `APP_NAME`.
3) Verify 2FA
   - Go to `/verify-2fa` and enter the 6‑digit code from your authenticator app.
   - On success, 2FA is enabled for your account and you're logged in.
4) Login thereafter
   - Visit `/login`, submit username/password, then confirm with your current 6‑digit code at `/verify-2fa`.

Protected home page: `/`.

---

## Configuration overview
- `config.py`
  - `DevelopmentConfig` (default), `TestingConfig`, and `ProductionConfig`
  - Defaults: `DATABASE_URL=sqlite:///dev.sqlite`, `APP_NAME=Flask2FA`
- `src/__init__.py`
  - Loads config from `APP_SETTINGS` or defaults to `config.DevelopmentConfig`
- `.env.example`
  - Copy to `.env` for local overrides

---

## Common issues & troubleshooting
- ModuleNotFoundError: No module named 'decouple'
  - Ensure you're using the virtual environment’s Python and that `python-decouple` is installed.
  - If you installed a conflicting package named `decouple` (not `python-decouple`), uninstall it:
    ```powershell
    .\venv\Scripts\python.exe -m pip uninstall decouple
    ```
- ModuleNotFoundError: No module named 'PIL'
  - Pillow provides PIL. Install it (already in `requirements.txt`):
    ```powershell
    pip install Pillow
    ```
- sqlite3.OperationalError: no such table: users
  - Run migrations:
    ```powershell
    .\venv\Scripts\python.exe .\manage.py db migrate -m "create users table"
    .\venv\Scripts\python.exe .\manage.py db upgrade
    ```
- Could not locate a Flask application (Flask CLI)
  - Always run via the provided CLI entry:
    ```powershell
    .\venv\Scripts\python.exe .\manage.py run
    ```
  - Avoid using system `python` outside the virtual environment.

---

## Project structure
```
config.py
manage.py
requirements.txt
src/
  __init__.py
  utils.py
  accounts/
    forms.py
    models.py
    views.py
  core/
    views.py
  static/
    styles.css
  templates/
    _base.html
    navigation.html
    accounts/
      login.html
      register.html
      setup-2fa.html
      verify-2fa.html
    core/
      index.html
```

---

## Security notes
- Keep `SECRET_KEY` secret in production.
- Use Postgres or another production‑grade DB and set `DATABASE_URL` accordingly.
- Consider HTTPS everywhere when deploying.

---

## Tests
Run the automated test suite (includes a dead-link crawler):

```powershell
.\venv\,Scripts\python.exe -m pytest -q
```

The dead link test requests public pages, follows redirects, extracts internal anchor hrefs, and fails if any return HTTP status >= 400.

Extend coverage by adding authenticated pages: create a helper that registers + logs in a user, then seeds additional paths.

Project test files:
```
tests/
  conftest.py        # Pytest fixtures & temporary DB setup
  test_dead_links.py # Crawls pages & checks for failing status codes
```

---

## License
This project is licensed under the terms of the LICENSE file included in this repository.
