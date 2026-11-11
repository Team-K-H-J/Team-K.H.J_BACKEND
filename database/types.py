from sqlalchemy import DateTime
from sqlalchemy.dialects.mysql import DATETIME

# Keep event ordering at subsecond precision in MySQL; store UTC without tzinfo.
UTCDateTime = DateTime().with_variant(DATETIME(fsp=6), "mysql")
