from sqlalchemy import BIGINT, Column, Date, DateTime, Float, Integer, Sequence, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
TABLE_PREFIX = "catalogue_"


class CatalogueItem(Base):
    __tablename__ = f"{TABLE_PREFIX}catalogueitem"
    uuid = Column(String, primary_key=True)
    name = Column(String)
    content_length = Column(BIGINT)
    ingestion_date = Column(DateTime)
    contentdate_start = Column(DateTime)
    contentdate_end = Column(DateTime)
    checksum_algorithm = Column(String)
    checksum_value = Column(String)


class TransferInfo(Base):
    __tablename__ = f"{TABLE_PREFIX}transfer_info"
    transfer_id = Column(String, primary_key=True)
    catalogue_uuid = Column(String)
    status = Column(String)
    started_on = Column(DateTime)
    completed_on = Column(DateTime)
