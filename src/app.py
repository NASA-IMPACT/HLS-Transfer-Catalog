import os
import uuid

import pandas as pd
from flask import Flask, abort, g, jsonify, request
from flask_cors import CORS
from loguru import logger

from src.config import CONFIG_BY_ENV
from src.services.db.models import CatalogueItem, db
from src.utils import abort_json, clean_files

ENV = os.getenv("FLASK_ENV", "local")

# TODO: Raise error if values not set
CFG = CONFIG_BY_ENV[os.getenv("FLASK_ENV", "local")]
DB_URI = f"{CFG.DB_TYPE}://{CFG.DB_USER}:{CFG.DB_PASSWORD}@{CFG.DB_HOST}:{CFG.DB_PORT}/{CFG.DB_NAME}"

logger.info("Starting the server...")
app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI

CORS(app)

db.init_app(app)
with app.app_context():
    logger.info("Creating all tables...")
    db.create_all()
    logger.info("Created tables..")


logger.info("Server up and running...")


@app.route("/catalogue/upload/", methods=["POST"])
def upload_csv():
    """
    Endpoint to upload CSV and update catalogeitem table

    TODO:
        - sanity check csv column names
    """
    logger.info("/catalogue/upload/ POST called")
    fname = uuid.uuid4().hex
    fpath = os.path.join("tmp", f"{fname}.csv")
    body = request.files["csv"]
    body.save(fpath)

    logger.debug("Normalizing column names...")
    try:
        data = pd.read_csv(fpath)
    except:
        logger.error("Failed to load csv")
        clean_files([fpath])
        abort_json(400, error="INVALID_FILE")
    data.rename(
        columns={
            "Id": "uuid",
            "Name": "name",
            "ContentLength": "content_length",
            "IngestionDate": "ingestion_date",
            "ContentDate:Start": "content_date_start",
            "ContentDate:End": "content_date_end",
            "Checksum:Algorithm": "checksum_algorithm",
            "Checksum:Value": "checksum_value",
        },
        inplace=True,
    )
    logger.debug("Dumping to table={CatalogueItem.__tablename__}")
    try:
        _ = data.to_sql(
            name=CatalogueItem.__tablename__,
            con=db.engine,
            index=False,
            if_exists="replace",
        )
    except:
        logger.error("CatalogueItem table upload failed")
        clean_files([fpath])
        abort_json(400, error="UPLOAD_FAILED")
    logger.debug("CatalogueItem table updated Successfully!")

    clean_files([fpath])
    return jsonify({"message": "success"}), 200


@app.route("/health/", methods=["GET"])
def health():
    return "Catalogue server v1 api!"


if __name__ == "__main__":
    app.run()
