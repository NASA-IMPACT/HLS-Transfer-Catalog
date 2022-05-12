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
- `JWT_SECRET_KEY`
- JWT_TOKEN_EXPIRATION_SECONDS (defaults to 300 seconds)

## Run

Run gunicorn : `gunicorn --bind 0.0.0.0:$PORT --workers=1 --threads=8 src.app:app --timeout=900`
[make sure to set the port to anything (like: 8000)]

# API Request test

Currently, we provide full CRUD REST api for the catalog tables.

(Note: Following curl examples are for local server. Please, change the endpooints accordingly to point to remote.)

## 1) /catalogue/bulk/csv - POST, Upload CSV

Enables anyone to upload csv of specific format to populate the catalogue table in bulk.

```bash
curl --location --request POST 'http://127.0.0.1:5000/catalogue/bulk/csv/' \
--header 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoidWRheSIsInBhc3N3b3JkIjoidWRheSIsImV4cCI6MTY1MjMzNTgzNn0.UfKN62xWmsXTzwy7tmRbP6I9DbrtXMnidQFFLq6epfs' \
--form 'csv=@"/Users/udaykumarbommala/Downloads/test.csv"
```

## 2) /catalogue/ - GET, all items

Enables anyone to fetch catalogue metadata items. We can use 2 query params to filter the result:
- `transfer_status` - NOT_STARTED/COMPLETED/FAILED/IN_PROGRESS
- `page` - Used for pagination


```bash
curl --location --request GET 'http://127.0.0.1:5000/catalogue/?transfer_status=NOT_STARTED' \
--header 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoidWRheSIsInBhc3N3b3JkIjoidWRheSIsImV4cCI6MTY1MjMzNTgzNn0.UfKN62xWmsXTzwy7tmRbP6I9DbrtXMnidQFFLq6epfs'
```

## 3)  /catalogue/uuid/ - GET single item

```bash
curl --location --request GET 'http://127.0.0.1:5000/catalogue/6a1f5438-50d1-4e02-a11b-52f9018da69f/' \
--header 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoidWRheSIsInBhc3N3b3JkIjoidWRheSIsImV4cCI6MTY1MjMzNTgzNn0.UfKN62xWmsXTzwy7tmRbP6I9DbrtXMnidQFFLq6epfs'
```

## 4) /catalogue/ - POST single item

This  is used to create a single catalogue item to the database

```bash
curl --location --request POST 'http://127.0.0.1:5000/catalogue/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoidWRheSIsInBhc3N3b3JkIjoidWRheSIsImV4cGlyYXRpb24iOiIyMDIyLTA3LTEwIDAxOjQ5OjEwLjQ4MDY0OCIsImFsZ29yaXRobSI6IkhTMjU2In0.T2UNUeZkqtZcV11LgKkGSc92RSN9aqui0cloz_ef7JY' \
--header 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoidWRheSIsInBhc3N3b3JkIjoidWRheSIsImV4cCI6MTY1MjMzNTgzNn0.UfKN62xWmsXTzwy7tmRbP6I9DbrtXMnidQFFLq6epfs' \
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
curl --location --request PATCH 'http://127.0.0.1:5000/catalogue/c266dc7b9fad4d64aaa7d103b6f0af09/' \
--header 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoidWRheSIsInBhc3N3b3JkIjoidWRheSIsImV4cCI6MTY1MjMzNTgzNn0.UfKN62xWmsXTzwy7tmRbP6I9DbrtXMnidQFFLq6epfs' \
--header 'Content-Type: application/json' \
--data-raw '{
    "name": "test",
    "transfer_status": "failed"
}'
```

## 6) /catalogue/uuid/ - DELETE single item

Delets a given catalogue item

```bash
curl --location --request DELETE 'http://127.0.0.1:5000/catalogue/8e547de43cbf43a3a50dffb81d255bb2/' \
--header 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoidWRheSIsInBhc3N3b3JkIjoidWRheSIsImV4cCI6MTY1MjMzNTgzNn0.UfKN62xWmsXTzwy7tmRbP6I9DbrtXMnidQFFLq6epfs'
```


## 7) /catalogue/bulk/ - PATCH multiple items

Used for updating multiple items in a single request.

```bash
curl --location --request PATCH 'http://127.0.0.1:5000/catalogue/bulk/' \
--header 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoidWRheSIsInBhc3N3b3JkIjoidWRheSIsImV4cCI6MTY1MjMzNTgzNn0.UfKN62xWmsXTzwy7tmRbP6I9DbrtXMnidQFFLq6epfs' \
--header 'Content-Type: application/json' \
--data-raw '{
    "abcdef": {}
}'
```

Here the json data posted is of the structure:
```json
{
    <uuid1>: {<json>},
    <uuid2>: {<json>},
}
```

## 8) /auth/login/ - POST Generate JWT Token

Used for generating JWT token based on user credentails
```bash
curl --location --request POST 'http://127.0.0.1:5000/auth/login/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "username": "username",
    "password": "password"
}'
```
