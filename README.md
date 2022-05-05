# Catalog
Catalog for ESA data transfer study


# Setup

## Dependency

System dependency of `postgresql`.

For python-specific dependency, see `requirements.txt`.

## Installation

- Install postgresql
- create a virtualenv : `python -m venv venv/`
- activate venv: `source venv/bin/activate`
- Install python dependency: `pip install -r requirements.txt`

## Database configuration

Make sure, you have a database configured with proper username/password.

You can either edit `src/config.py` to override the config values for `LocalConfig`.

Or, set environment variables:
- `DB_HOST`
- `DB_PORT` (defaults to 5432)
- `DB_NAME` (defaults to "tempdb" for local config)
- `DB_USER`
- `DB_PASSWORD`
- `DB_TYPE` (defaults to "postgresql")

## Run

Run gunicorn : `gunicorn --bind 0.0.0.0:$PORT --workers=1 --threads=8 src.app:app --timeout=900`
[make sure to set the port to anything (like: 8000)]

# Request test

There are few endpoints currently:

# 1) `/catalogue/upload/` - POST

Enables anyone to upload csv of specific format to populate the catalogue table)

```bash
curl --location --request POST 'http://localhost:8000/catalogue/upload/' \
--form 'csv=@"<path to csv>"'
```

# 2) `/catalogue/` - GET

enables anyone to fetch catalogue metadata items. It also has `start_date` and `ènd_date` query filter)


```bash
curl --location --request GET 'http://localhost:8000/catalogue/?start_date=2021-11-01&end_date=2021-12-12'
```
