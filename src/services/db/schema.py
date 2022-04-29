from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field, fields

from .models import CatalogueItem


class CatalogueItemSchema(SQLAlchemySchema):
    class Meta:
        model = CatalogueItem
        load_instance = True

    uuid = auto_field()
    name = auto_field()
    ingestion_date = fields.fields.String()
    content_date_start = fields.fields.String()
    content_date_end = fields.fields.String()
    checksum_algorithm = auto_field()
    checksum_value = auto_field()
