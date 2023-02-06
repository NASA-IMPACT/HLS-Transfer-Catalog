from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field, fields

from .models import CatalogueItem


class CatalogueItemSchema(SQLAlchemySchema):
    """
    This is used for serialization
    """

    class Meta:
        model = CatalogueItem
        load_instance = True

    uuid = auto_field()
    source_path = fields.fields.String()
    destination_path = fields.fields.String()
    ingestion_date = fields.fields.String()
    content_date_start = fields.fields.String()
    content_date_end = fields.fields.String()
    checksum_algorithm = auto_field()
    checksum_value = auto_field()

    transfer_id = auto_field()
    transfer_status = auto_field()
    transfer_checksum_value = auto_field()
    transfer_checksum_verification = auto_field()
    transfer_started_on = fields.fields.String()
    transfer_completed_on = fields.fields.String()
    transfer_source = auto_field()
    transfer_destination = auto_field()

    sealed_state = auto_field()
    unseal_time = fields.fields.String()
    unseal_expiry_time = fields.fields.String()

    source_storage_id = fields.fields.String()
    dest_storage_id = fields.fields.String()

    created_on = fields.fields.String()
    updated_on = fields.fields.String()
