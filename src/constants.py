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
}
