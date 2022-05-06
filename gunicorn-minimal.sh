#!/usr/bin/env bash

gunicorn --bind 0.0.0.0:$PORT --workers=1 --threads=8 src.app:app --timeout=900
