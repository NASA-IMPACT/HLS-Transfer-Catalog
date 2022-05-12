import os
from functools import wraps
from typing import List

import jwt
from flask import abort, jsonify, request
from loguru import logger

from src.config import CONFIG_BY_ENV

CFG = CONFIG_BY_ENV[os.getenv("FLASK_ENV", "local")]


def clean_files(paths: List[str]) -> bool:
    for path in paths:
        try:
            os.remove(path)
        except FileNotFoundError:
            logger.warning(f"Failed to remove path={path}")


def abort_json(status_code, error="", message="", status="fail"):
    response = jsonify(
        {
            "status": status,
            "message": message,
            "error": error,
            "status_code": status_code,
        }
    )
    logger.error(
        "| {message} || backend-{code} || {data} |".format(
            message=error, data=message, code=status_code
        )
    )
    response.status_code = status_code
    abort(response)


def token_required(func):
    # decorator factory which invoks update_wrapper() method and passes decorated function as an argument
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers.get("token")
        if not token:
            abort_json(
                400,
                error="AUTHENTICATION_FAILED",
                message="Token is missing!",
            )
        try:
            logger.info("Validating JWT token")
            data = jwt.decode(token, CFG.JWT_SECRET_KEY, algorithms="HS256")
        except jwt.ExpiredSignatureError:
            abort_json(
                403,
                error="AUTHENTICATION_FAILED",
                message="Token Expired!",
            )
        except:
            abort_json(
                403,
                error="AUTHENTICATION_FAILED",
                message="Invalid token!",
            )
        return func(*args, **kwargs)

    return decorated
