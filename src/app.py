import os
import traceback
import uuid
from datetime import datetime, timedelta

import jwt
import pandas as pd
from dateutil import parser as dt_parser
from flask import Flask, abort, g, jsonify, request
from flask_cors import CORS
from loguru import logger
from sqlalchemy import and_, asc

import src.constants as CONSTANTS
from src.config import CONFIG_BY_ENV
from src.services.db.enums import SealedStatus, TransferStatus
from src.services.db.models import CatalogueItem, CatalogueArchiveItem, db
from src.services.db.schema import CatalogueItemSchema
from src.utils import abort_json, clean_files, token_required

ENV = os.getenv("FLASK_ENV", "local")

# TODO: Raise error if values not set
CFG = CONFIG_BY_ENV[os.getenv("FLASK_ENV", "local")]

DB_URI = f"{CFG.DB_TYPE}://{CFG.DB_USER}:{CFG.DB_PASSWORD}@{CFG.DB_HOST}:{CFG.DB_PORT}/{CFG.DB_NAME}"

ERROR_MSG_ANY_OF_THE_CATALOGUE_POST_MANDATORY_FIELDS_EMPTY = (
    "Any of the column "
    + ",".join(CONSTANTS.CATALOGUE_POST_MANDATORY_FIELDS)
    + "values are empty!"
)

ALLOWED_EXTENSIONS = CFG.ALLOWED_EXTENSIONS

logger.info("Starting the server...")
app = Flask(__name__)
app.config["FLASK_ENV"] = ENV
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
#@token_required
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
#@token_required
def list_catalogue():
    """
    This API is used to select the CatalogueItem table based on query fitlers:
        - transfer_status (reference: `services.db.enums.TransferStatus`)
        - sealed_state (reference: `services.db.enums.SealedStatus`)
        - page (used for pagination)
    """
    logger.info("/catalogue/ - GET called")
    transfer_status = (
        request.args.get("transfer_status", TransferStatus.NOT_STARTED.value)
        .strip()
        .upper()
    )
    sealed_status = (
        request.args.get("sealed_state", SealedStatus.PERMANENT_UNSEALED.value)
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

    logger.debug(f"raw transfer_status = {request.args.get('transfer_status')}")
    logger.debug(f"raw sealed_state = {request.args.get('sealed_state')}")

    logger.debug(f"page = {page}")
    logger.debug(f"status = {transfer_status}")
    logger.debug(f"state = {sealed_status}")

    res = (
        CatalogueItem.query.filter(
            and_(
                CatalogueItem.transfer_status == transfer_status,
                CatalogueItem.sealed_state == sealed_status,
            )
        )
        .order_by(asc(CatalogueItem.unseal_expiry_time))
        .paginate(page=page, per_page=CFG.ITEMS_PER_PAGE, error_out=False)
    )
    res = CatalogueItemSchema(many=True).dump(res.items)
    logger.debug(f"Total rows selected = {len(res)}")

    return jsonify(res)


@app.route("/catalogue/count/", methods=["GET"])
#@token_required
def catalogue_count():
    """
    This API is used to get the count of CatalogueItem table based on query fitlers:
        - transfer_status (reference: `services.db.enums.TransferStatus`)
        - sealed_state (reference: `services.db.enums.SealedStatus`)
    """
    logger.info("/catalogue/count/ - GET called")
    status = (
        request.args.get("transfer_status", TransferStatus.NOT_STARTED.value)
        .strip()
        .upper()
    )
    state = (
        request.args.get("sealed_state", SealedStatus.PERMANENT_UNSEALED.value)
        .strip()
        .upper()
    )
    try:
        res = CatalogueItem.query.filter(
            and_(
                CatalogueItem.transfer_status == status,
                CatalogueItem.sealed_state == state,
            )
        ).count()
    except:
        abort_json(
            400,
            error="FECTHING_FAILED",
            message="Unable to fetch the catalogue item count.",
        )
    return jsonify(dict(count=res))


@app.route("/catalogue/", methods=["POST"])
#@token_required
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
#@token_required
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
#@token_required
def delete_catalogue(uuid: str):
    item = CatalogueItem.query.filter_by(uuid=uuid).first()
    if not item:
        logger.error(f"Item for uuid={uuid} not found!")
        abort_json(404, error="DELETION_FAILED", message="uuid doesn't exist!")

    res = CatalogueItemSchema().dump(item)
    db.session.delete(item)
    db.session.commit()
    return jsonify(res)

@app.route("/catalogue/", methods=["DELETE"])
def delete_all_catalogue():
    db.session.query(CatalogueItem).delete()
    db.session.commit()
    return (
        jsonify(
            {
                "message": "All the records got successufully deleted"
            }
        ),
        200,
    )

@app.route("/catalogue/bulk/", methods=["PATCH"])
#@token_required
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

    return jsonify(dict(failed=failed, success=success))


@app.route("/catalogue/bulk/csv/", methods=["POST"])
#@token_required
def upload_csv():
    """
    Endpoint to upload CSV/ZIP and update catalogeitem table

    This only accepts a csv/zip file with following columns (strictly):
        - Id (unique identifier to the file)
        - Name
        - ContentLength
        - IngestionDate
        - ContentDate:Start
        - ContentDate:End
        - Checksum:Algorithm
        - Checksum:Value
        - IsSealed
    TODO:
        - optimize csv loader for a very large CSV
        - optimize csv dump to database
        - async upload
    """
    logger.info("/catalogue/upload/ POST called")
    file = request.files["file"]
    fextension = file.filename.rsplit('.', 1)[1].lower()
    if fextension not in ALLOWED_EXTENSIONS:
        abort_json(400, error="INVALID_FILE_EXTENSION")
    fname = uuid.uuid4().hex
    fpath = ""
    if file.filename == '':
        abort_json(400, error="INVALID_FILE")
    if fextension == 'csv':
        fpath = os.path.join("tmp", f"{fname}.csv")
    else:
        fpath = os.path.join("tmp", f"{fname}.zip")
    file.save(fpath)

    try:
        data = pd.read_csv(fpath)
    except:
        logger.error("Failed to load csv")
        clean_files([fpath])
        abort_json(400, error="INVALID_FILE")

    try:
        data.rename(
            columns=CONSTANTS.CATALOGUE_CSV_COLUMN_MAPPER, inplace=True, errors="raise"
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
    if data[CONSTANTS.CATALOGUE_POST_MANDATORY_FIELDS].isna().sum().sum() > 0:
        logger.error(ERROR_MSG_ANY_OF_THE_CATALOGUE_POST_MANDATORY_FIELDS_EMPTY)
        clean_files([fpath])
        abort_json(
            400,
            error="UPLOAD_FAILED",
            message=ERROR_MSG_ANY_OF_THE_CATALOGUE_POST_MANDATORY_FIELDS_EMPTY,
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
    data["transfer_id"] = ""
    data["transfer_status"] = "NOT_STARTED"
    data["transfer_checksum_value"] = ""
    data["transfer_checksum_verification"] = ""
    data["transfer_started_on"] = CONSTANTS.DATETIME_OLDEST
    data["transfer_completed_on"] = CONSTANTS.DATETIME_OLDEST
    data["transfer_source"] = ""
    data["transfer_destination"] = ""

    data["sealed_state"] = data["sealed_state"].map(
        CONSTANTS.CATALOGUE_SEALED_STATE_MAPPER
    )

    data["created_on"] = datetime.now()
    data["updated_on"] = datetime.now()

    uuids = list(data["uuid"])
    items = list(map(lambda d: CatalogueItem(**d), data.to_dict("records")))

    logger.debug(f"Dumping to table={CatalogueItem.__tablename__}")

    failed = []
    try:

        existing_data = CatalogueItem.query.filter(CatalogueItem.uuid.in_(uuids))
        existing_uuids = set(map(lambda d: d.uuid, existing_data))

        to_add_uuids = set(uuids) - existing_uuids
        to_add_data = list(filter(lambda item: item.uuid in to_add_uuids, items))
        db.session.add_all(to_add_data)
        db.session.commit()

        failed = list(existing_uuids)
        logger.debug(f"{len(to_add_data)}/{len(uuids)} data added.")
    except:
        logger.error("CatalogueItem table upload failed")
        abort_json(400, error="UPLOAD_FAILED", message="Dumping to sql table failed!")
    finally:
        clean_files([fpath])
    logger.info("CatalogueItem table updated Successfully!")
    return (
        jsonify(
            {
                "message": "success",
                "failed": {"count": len(failed), "uuids": failed},
            }
        ),
        200,
    )

@app.route("/catalogue/archive/records/", methods=["POST"])
def archive_catalogue_records():
    logger.info("/catalogue/archive/records/ POST called")
    container_name = (
        request.args.get("container_name")
    )
    if not container_name.strip():
       return abort_json(400, error="REQUEST_FAILED", message="Please enter container name!")
    try:
        query = "INSERT INTO {} SELECT * FROM {} WHERE source_storage_id='{}';".format(CatalogueArchiveItem.__tablename__, CatalogueItem.__tablename__, container_name)
        logger.info(f"query: {query}")
        db.session.execute(query)
        db.session.commit()
    except:
        logger.error("Archiving the records to archive table got failed")
        abort_json(400, error="ARCHIVE_FAILED", message="Archiving records to archive table failed!")
    logger.info("CatalogueArchiveItem table updated Successfully!")
    return (
        jsonify(
            {
                "message": "All the records got successufully archived into archive table"
            }
        ),
        200,
    )

@app.route("/health/", methods=["GET"])
def health():
    return "Catalogue server v1 api!"


if __name__ == "__main__":
    app.run()
