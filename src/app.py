import os
import uuid

import pandas as pd
from flask import Flask, abort, g, jsonify, request
from loguru import logger

from src.services.db.models2 import CatalogueItem, db

DB_PORT = os.getenv("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME", "tempdb")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASS")
DB_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}"

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
logger.info("Starting the server...")

db.init_app(app)

with app.app_context():
    logger.info("Creating all tables...")
    db.create_all()
    logger.info("Created tables..")


logger.info("Server up and running...")


@app.route("/test", methods=["GET"])
def test():
    data = CatalogueItem.query.all()
    print(data)
    return "Catalogue server v1 api!"


@app.route("/catalogue/upload/", methods=["POST"])
def upload_csv():
    logger.info("/catalogue/upload/ POST called")
    fname = uuid.uuid4().hex
    fpath = os.path.join("tmp", f"{fname}.csv")
    body = request.files["csv"]
    body.save(fpath)

    logger.debug("Normalizing column names...")
    data = pd.read_csv(fpath)
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
    _ = data.to_sql(
        name=CatalogueItem.__tablename__,
        con=db.engine,
        index=False,
        if_exists="replace",
    )
    logger.debug("Successful!")
    return "success"


@app.route("/health/", methods=["GET"])
def health():
    return "Catalogue server v1 api!"


if __name__ == "__main__":
    app.run()
