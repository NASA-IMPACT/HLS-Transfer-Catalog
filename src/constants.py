import datetime

from src.services.db.enums import SealedStatus

CATALOGUE_POST_MANDATORY_FIELDS = [
    "name",
    "checksum_algorithm",
    "checksum_value",
]

CATALOGUE_CSV_COLUMN_MAPPER = {
    "Id": "uuid",
    "Name": "name",
    "ContentLength": "content_length",
    "IngestionDate": "ingestion_date",
    "ContentDate:Start": "content_date_start",
    "ContentDate:End": "content_date_end",
    "Checksum:Algorithm": "checksum_algorithm",
    "Checksum:Value": "checksum_value",
    "IsSealed": "sealed_state",
}

CATALOGUE_SEALED_STATE_MAPPER = {
    True: SealedStatus.SEALED.value,
    False: SealedStatus.PERMANENT_UNSEALED.value,
    "TRUE": SealedStatus.SEALED.value,
    "FALSE": SealedStatus.PERMANENT_UNSEALED.value,
    "true": SealedStatus.SEALED.value,
    "false": SealedStatus.PERMANENT_UNSEALED.value,
}

DATETIME_OLDEST = datetime.datetime(year=1970, month=1, day=1)
