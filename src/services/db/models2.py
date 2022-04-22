from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

TABLE_PREFIX = "catalogue_"


class CatalogueItem(db.Model):
    __tablename__ = f"{TABLE_PREFIX}catalogueitem"
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    content_length = db.Column(db.BIGINT)
    ingestion_date = db.Column(db.DateTime)
    content_date_start = db.Column(db.DateTime)
    content_date_end = db.Column(db.DateTime)
    checksum_algorithm = db.Column(db.String)
    checksum_value = db.Column(db.String)


class TransferInfo(db.Model):
    __tablename__ = f"{TABLE_PREFIX}transfer_info"
    transfer_id = db.Column(db.String, primary_key=True)
    catalogue_uuid = db.Column(db.String)
    status = db.Column(db.String)  # IN-PROGRESS/COMPLETED/TODO
    checksum_verification = db.Column(db.String(10))  # GOOD/BAD
    started_on = db.Column(db.DateTime)
    completed_on = db.Column(db.DateTime)
    source = db.Column(db.String, nullable=True)  # ESA/NASA?
    destination = db.Column(db.String, nullable=True)  # ESA/NASA
