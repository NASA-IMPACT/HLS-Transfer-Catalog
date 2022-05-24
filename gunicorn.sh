#!/usr/bin/env bash

if [[ "$FLASK_ENV" != null && "$FLASK_ENV" != "local" ]];
then
    export SECRETS=$(aws secretsmanager get-secret-value --secret-id $SECRET --region us-east-1 | jq -c '.SecretString | fromjson')
    export DB_HOST=$(echo $SECRETS | jq -r .host)
    export DB_USER=$(echo $SECRETS | jq -r .username)
    export DB_NAME=$(echo $SECRETS | jq -r .dbname)
    export DB_PORT=$(echo $SECRETS | jq -r .port)

    # Setting this environment variable to surpass a psql password prompt
    export DB_PASSWORD=$(echo $SECRETS | jq -r .password)

    gunicorn --bind 0.0.0.0:$PORT --workers=1 --threads=8 src.app:app --timeout=900 &

    nginx -g "daemon off;"
else
    gunicorn --bind 0.0.0.0:$PORT --workers=1 --threads=8 src.app:app --timeout=900
fi
