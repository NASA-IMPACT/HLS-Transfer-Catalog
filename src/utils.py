import os
from typing import List

from flask import abort, jsonify
from loguru import logger


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
