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
- `ITEMS_PER_PAGE` (defaults to 1000)

## Run

Run gunicorn : `gunicorn --bind 0.0.0.0:$PORT --workers=1 --threads=8 src.app:app --timeout=900`
[make sure to set the port to anything (like: 8000)]

# API Request test

Currently, we provide full CRUD REST api for the catalog tables.

(Note: Following curl examples are for local server. Please, change the endpooints accordingly to point to remote.)

## 1) /catalogue/bulkd/csv - POST, Upload CSV

Enables anyone to upload csv of specific format to populate the catalogue table in bulk.

```bash
curl --location --request POST 'http://localhost:8000/catalogue/bulk/csv/' \
--form 'csv=@"/Users/nishparadox/Downloads/test.csv"'
```

## 2) /catalogue/ - GET, all items

Enables anyone to fetch catalogue metadata items. We can use 2 query params to filter the result:
- `transfer_status` - NOT_STARTED/COMPLETED/FAILED/IN_PROGRESS
- `page` - Used for pagination


```bash
curl --location --request GET 'http://localhost:8000/catalogue/?page=1&transfer_status=NOT_STARTED'
```

## 3)  /catalogue/uuid/ - GET single item

```bash
curl --location --request GET 'http://localhost:8000/catalogue/testid123/'
```

## 4) /catalogue/ - POST single item

This  is used to create a single catalogue item to the database

```bash
curl --location --request POST 'http://localhost:8000/catalogue/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "uuid": "8e547de43cbf43a3a50dffb81d255bb2",
    "transfer_status": "failed",
    "name": "test",
    "checksum_algorithm": "test",
    "checksum_value": "test"
}'
```

> Note: The json data should have `name`, `checksum_value` and `checksum_algorithm` mandatory. If `uuid is provided in the json data, it will be re-used. If not, new uuid will be created.`

## 5) /catalogue/uuid/ - PATCH single item

Used for updating a specific catalogue item referenced by the given uuid.

```bash
curl --location --request PATCH 'http://localhost:8000/catalogue/testid123/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "name": "test",
    "transfer_status": "NOT_STARTED"
}'
```

## 6) /catalogue/uuid/ - DELETE single item

Delets a given catalogue item

```
curl --location --request DELETE 'http://localhost:8000/catalogue/testid123/'
```


## 7) /catalogue/bulk/ - PATCH multiple items

Used for updating multiple items in a single request.

```bash
curl --location --request PATCH 'http://localhost:8000/catalogue/bulk/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "abcde": {}
}'
```

Here the json data posted is of the structure:
```json
{
    <uuid1>: {<json>},
    <uuid2>: {<json>},
}
```
