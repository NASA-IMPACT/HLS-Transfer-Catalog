from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

TABLE_PREFIX = "catalogue_"


class CatalogueItem(db.Model):
    """
    This is the metadata information for each file
    to be transferred.

    Ingestion date is when the file was processed/added to the dataset.
    Content start/end is when the data was sensed.

    The column prefixed with "transfer_" are used to track transfer info.

    """

    __tablename__ = f"{TABLE_PREFIX}catalogue_item"
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    content_length = db.Column(db.BIGINT)
    ingestion_date = db.Column(db.DateTime)
    content_date_start = db.Column(db.DateTime)
    content_date_end = db.Column(db.DateTime)
    checksum_algorithm = db.Column(db.String)
    checksum_value = db.Column(db.String)

    transfer_status = db.Column(
        db.String, default="NOT_STARTED"
    )  # NOT_STARTED/IN_PROGRESS/COMPLETED/FAILED
    transfer_checksum_value = db.Column(db.String, nullable=True)
    transfer_checksum_verification = db.Column(db.String(20), nullable=True)
    transfer_started_on = db.Column(db.DateTime, nullable=True)
    transfer_completed_on = db.Column(db.DateTime, nullable=True)
    transfer_source = db.Column(db.String, nullable=True)
    transfer_destination = db.Column(db.String, nullable=True)

    def update(self, data: dict) -> None:
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)
