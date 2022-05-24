#!/usr/bin/env bash

gunicorn --bind 127.0.0.1:8080 --workers=1 --threads=8 src.app:app --timeout=900 &
