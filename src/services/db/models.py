from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

from .enums import TransferStatus

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

    transfer_id = db.Column(db.String)
    transfer_status = db.Column(
        db.String, default=TransferStatus.NOT_STARTED.value, index=True
    )
    transfer_checksum_value = db.Column(db.String, nullable=True)
    transfer_checksum_verification = db.Column(db.String(20), nullable=True)
    transfer_started_on = db.Column(db.DateTime, nullable=True)
    transfer_completed_on = db.Column(db.DateTime, nullable=True)
    transfer_source = db.Column(db.String, nullable=True)
    transfer_destination = db.Column(db.String, nullable=True)

    sealed_state = db.Column(db.String, index=True)
    unseal_time = db.Column(db.DateTime, nullable=True)
    unseal_expiry_time = db.Column(db.DateTime, nullable=True)

    source_storage_id = db.Column(db.String, index=True)
    dest_storage_id = db.Column(db.String, index=True)

    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(
        db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now()
    )

    def update(self, data: dict) -> None:
        """
        Update through external dict.
        """
        if not data:
            return
        data = data.copy()
        data.pop("uuid", None)
        data.pop("created_on", None)
        data.pop("updated_on", None)

        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)
                self.updated_on = datetime.now()
