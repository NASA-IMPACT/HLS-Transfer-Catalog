import os
import uuid
from datetime import datetime, timedelta

import jwt
import pandas as pd
from dateutil import parser as dt_parser
from flask import Flask, abort, g, jsonify, request
from flask_cors import CORS
from loguru import logger

import src.constants as CONSTANTS
from src.config import CONFIG_BY_ENV
from src.services.db.enums import TransferStatus
from src.services.db.models import CatalogueItem, db
from src.services.db.schema import CatalogueItemSchema
from src.utils import abort_json, clean_files, str_to_bool, token_required

ENV = os.getenv("FLASK_ENV", "local")

# TODO: Raise error if values not set
CFG = CONFIG_BY_ENV[os.getenv("FLASK_ENV", "local")]
CFG.DEBUG = str_to_bool(CFG.DEBUG)

DB_URI = f"{CFG.DB_TYPE}://{CFG.DB_USER}:{CFG.DB_PASSWORD}@{CFG.DB_HOST}:{CFG.DB_PORT}/{CFG.DB_NAME}"

logger.info("Starting the server...")
app = Flask(__name__)
app.config["DEBUG"] = CFG.DEBUG
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
app.config["SECRET_KEY"] = CFG.JWT_SECRET_KEY
app.config["JWT_TOKEN_EXPIRATION_SECONDS"] = CFG.JWT_TOKEN_EXPIRATION_SECONDS

CORS(app)

db.init_app(app)
with app.app_context():
    logger.info("Creating all tables...")
    db.create_all()
    logger.info("Created tables..")

os.makedirs("tmp", exist_ok=True)

logger.info("Server up and running...")

# TODO: Need to decide on the approach of single jwt token / individual jwt token based on user credentails
@app.route("/auth/login/", methods=["POST"])
def login():
    request_data = request.get_json()
    if request_data["username"] and request_data["password"]:
        logger.info("Generating JWT Token")
        token = jwt.encode(
            {
                "user": request_data["username"],
                "password": request_data["password"],
                "exp": datetime.utcnow()
                + timedelta(seconds=app.config["JWT_TOKEN_EXPIRATION_SECONDS"]),
            },
            app.config["SECRET_KEY"],
            "HS256",
        )
        return jsonify({"token": token})
    else:
        abort_json(403, error="AUTHENTICATION_FAILED", message="Unable to verify")


@app.route("/catalogue/<uuid>/", methods=["GET"])
@token_required
def get_catalogue(uuid: str):
    """
    GET single item from the database
    """
    logger.info("/catalogue/<uuid> GET called")
    res = CatalogueItem.query.filter_by(uuid=uuid).first()
    if not res:
        abort_json(404, error="DATA_NOT_FOUND", message="Item not found!")
    res = CatalogueItemSchema().dump(res)
    return jsonify(res)


@app.route("/catalogue/", methods=["GET"])
@token_required
def list_catalogue():
    """
    This API is used to select the CatalogueItem table based on query fitlers:
        - transfer_status (reference: `services.db.enums.TransferStatus`)
        - page (used for pagination)
    """
    logger.info("/catalogue/ - GET called")
    status = (
        request.args.get("transfer_status", TransferStatus.NOT_STARTED.value)
        .strip()
        .upper()
    )

    page = 1
    try:
        page = int(request.args.get("page", 1))
    except:
        if app.config.get("DEBUG", False):
            logger.warning("Defaulting page to 1")
        page = 1

    logger.debug(f"page = {page}")
    logger.debug(f"status = {status}")

    res = CatalogueItem.query.filter_by(transfer_status=status).paginate(
        page=page,
        per_page=CFG.ITEMS_PER_PAGE,
        error_out=False,
    )
    res = CatalogueItemSchema(many=True).dump(res.items)
    logger.debug(f"Total rows selected = {len(res)}")

    return jsonify(res)


@app.route("/catalogue/", methods=["POST"])
@token_required
def create_catalogue():
    """
    Create single catalog item record and return the created record.
    """
    logger.info("/catalogue/ POST called")
    data = request.json

    for field in CONSTANTS.CATALOGUE_POST_MANDATORY_FIELDS:
        if field not in data:
            abort_json(
                400,
                error="INSERTION_FAILED",
                message=f"Missing '{field}' in the json body...",
            )
    data["uuid"] = data.get("uuid", uuid.uuid4().hex)
    data["created_on"] = data.get("created_on", datetime.now())
    data["updated_on"] = data.get("updated_on", datetime.now())
    data["transfer_status"] = data.get("transfer_status", "NOT_STARTED").upper()

    query = CatalogueItem.query.filter_by(uuid=data["uuid"]).first()
    if query:
        abort_json(
            400,
            error="INSERTION_FAILED",
            message="uuid already exists!",
        )

    try:
        item = CatalogueItem(**data)
        db.session.add(item)
        db.session.commit()
    except:
        abort_json(
            400,
            error="INSERTION_FAILED",
            message="Unable to create the catalogue item.",
        )

    return jsonify(data)


@app.route("/catalogue/<uuid>/", methods=["PATCH"])
@token_required
def patch_catalogue(uuid: str):
    """
    Upsert a single catalogue item.
    """
    logger.info("/catalogue/<uuid> PATCH called")
    data = request.json

    item = CatalogueItem.query.filter_by(uuid=uuid).first()
    if not item:
        abort_json(404, error="PATCH_FAILED", message="uuid doesn't exist!")

    try:

        if "transfer_status" in data:
            data["transfer_status"] = data["transfer_status"].upper()
        item.update(data)
    except:
        abort_json(
            400,
            error="PATCH_FAILED",
            message="Unable to create the catalogue item.",
        )

    db.session.commit()
    return jsonify(CatalogueItemSchema().dump(item))


@app.route("/catalogue/<uuid>/", methods=["DELETE"])
@token_required
def delete_catalogue(uuid: str):
    item = CatalogueItem.query.filter_by(uuid=uuid).first()
    if not item:
        logger.error(f"Item for uuid={uuid} not found!")
        abort_json(404, error="DELETION_FAILED", message="uuid doesn't exist!")

    res = CatalogueItemSchema().dump(item)
    db.session.delete(item)
    db.session.commit()
    return jsonify(res)


@app.route("/catalogue/bulk/", methods=["PATCH"])
@token_required
def bulk_update_catalogue():
    """
    This API is used to bulk UPSERT the CatalogueItem values

    The expected JSON input to request is of the form:
        ..code-block:: json

            {
                <uuid1>: {<json>},
                <uuid2>: {<json>},
            }
    where uuid represents the catalogue item uuid value (unique) and json
    consists of fields and corresponding values to be updated.

    TODO:
        - sanity check timestamp?
        - convert datetime to datetime
    """
    data = request.json
    failed, success = [], []
    if data:
        # this will only give the data that "exists" in the table
        query = CatalogueItem.query.filter(CatalogueItem.uuid.in_(data.keys()))
        for item in query:
            try:
                item.update(data.get(item.uuid, {}))
                success.append(item.uuid)
            except:
                failed.append(item.uuid)
    db.session.commit()

    # get all thoese keys that weren't updated in the db
    failed = list(set(data.keys()) - set(success))
    logger.debug(f"success: {len(success)} | failed: {len(failed)}")

    return jsonify(dict(failed=failed, succes=success))


@app.route("/catalogue/bulk/csv/", methods=["POST"])
@token_required
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
        - optimize csv dump to database
        - async upload
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
            columns=CONSTANTS.CATALOGUE_CSV_COLUMN_MAPPER,
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
    data["transfer_started_on"] = CONSTANTS.DATETIME_OLDEST
    data["transfer_completed_on"] = CONSTANTS.DATETIME_OLDEST
    data["transfer_source"] = ""
    data["transfer_destination"] = ""

    data["created_on"] = datetime.now()
    data["updated_on"] = datetime.now()

    logger.debug(f"Dumping to table={CatalogueItem.__tablename__}")
    try:
        datarows = data.to_dict(orient="records")
        for d in datarows:
            item = CatalogueItem(**d)
            db.session.add(item)
            db.session.flush()
        db.session.commit()
    except:
        logger.error("CatalogueItem table upload failed")
        abort_json(400, error="UPLOAD_FAILED", message="Dumping to sql table failed!")
    finally:
        clean_files([fpath])
    logger.info("CatalogueItem table updated Successfully!")
    return jsonify({"message": "success"}), 200


@app.route("/health/", methods=["GET"])
def health():
    return "Catalogue server v1 api!"


if __name__ == "__main__":
    app.run()
