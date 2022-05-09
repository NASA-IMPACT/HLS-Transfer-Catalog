import os
import uuid

import pandas as pd
from dateutil import parser as dt_parser
from flask import Flask, abort, g, jsonify, request
from flask_cors import CORS
from loguru import logger

from src.config import CONFIG_BY_ENV
from src.services.db.models import CatalogueItem, db
from src.services.db.schema import CatalogueItemSchema
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

os.makedirs("tmp", exist_ok=True)

logger.info("Server up and running...")


# @app.route("/catalogue/", methods=["GET"])
# def list_catalogue():
#     start_date = request.args.get("start_date", "").strip()
#     end_date = request.args.get("end_date", "").strip()

#     try:
#         start_date = dt_parser.parse(start_date)
#     except:
#         logger.error("Failed to parse start_date...")
#         start_date = None

#     try:
#         end_date = dt_parser.parse(end_date)
#     except:
#         logger.error("Failed to parse end_date...")
#         end_date = None

#     logger.debug(f"start_date: {start_date}, end_date: {end_date}")

#     res = CatalogueItem.query
#     if start_date:
#         res = res.filter(CatalogueItem.ingestion_date >= start_date)
#     if end_date:
#         res = res.filter(CatalogueItem.ingestion_date <= end_date)
#     res = res.all()

#     res = CatalogueItemSchema(many=True).dump(res)
#     logger.debug(f"Total rows selected = {len(res)}")

#     return jsonify(res)


@app.route("/catalogue/", methods=["GET"])
def list_catalogue():
    """
    This API is used to select the CatalogueItem table based on quer fitlers:
        - status
    """
    logger.info("/catalogue/ - GET called")
    status = request.args.get("status", "NOT_STARTED").strip().upper()
    logger.debug(f"status = {status}")

    res = CatalogueItem.query.filter(CatalogueItem.transfer_status == status)
    res = CatalogueItemSchema(many=True).dump(res)
    logger.debug(f"Total rows selected = {len(res)}")

    return jsonify(res)


@app.route("/catalogue/upload/", methods=["POST"])
def upload_csv():
    """
    Endpoint to upload CSV and update catalogeitem table

    This only accepts a csv file with following columns (strictly):
        - Id (unique identifier to the file)
        - Name
        - ContentLength
        - IngestionDate
        - ContentDate:Start
        - ContentDate:End
        - Checksum:Algorithm
        - Checksum:Value

    TODO:
        - optimize csv loader for a very large CSV
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

    try:
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
    except:
        logger.error("Some columns are missing or improper column name.")
        clean_files([fpath])
        abort_json(
            400,
            error="UPLOAD_FAILED",
            message="Invalid columns or some columns are missing!",
        )

    # make sure these columns aren't empty
    if data[["uuid", "name"]].isna().sum().sum() > 0:
        logger.error("uuid or name column values are empty!")
        clean_files([fpath])
        abort_json(
            400, error="UPLOAD_FAILED", message="uuid or name column value empty!"
        )

    # in case content end date is missing, fill it up with start date
    data["content_date_end"].fillna(data["content_date_start"], inplace=True)
    try:
        data["content_date_start"] = pd.to_datetime(data["content_date_start"])
        data["content_date_end"] = pd.to_datetime(data["content_date_end"])
        data["ingestion_date"] = pd.to_datetime(data["ingestion_date"])
        # data["ingestion_date"] = data["ingestion_date"].apply(dt_parser.parse)
    except:
        logger.error(
            "Date time conversion failed for content_date_start and content_date_end columns! Aborting..."
        )
        clean_files([fpath])
        abort_json(
            400, error="UPLOAD_FAILED", message="Invalid ingestion/content-start date!"
        )

    # add transfer columns
    data["transfer_status"] = "NOT_STARTED"
    data["transfer_checksum_value"] = ""
    data["transfer_checksum_verification"] = ""
    data["transfer_started_on"] = ""
    data["transfer_completed_on"] = ""
    data["transfer_source"] = ""
    data["transfer_destination"] = ""

    logger.debug(f"Dumping to table={CatalogueItem.__tablename__}")
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
        abort_json(400, error="UPLOAD_FAILED", message="Dumping to sql table failed!")

    logger.info("CatalogueItem table updated Successfully!")

    clean_files([fpath])
    return jsonify({"message": "success"}), 200


@app.route("/health/", methods=["GET"])
def health():
    return "Catalogue server v1 api!"


if __name__ == "__main__":
    app.run()
