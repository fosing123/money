"""TIANA's tested Django adapter around the pg8000 database driver."""
from django_pg8000.base import DatabaseWrapper as Pg8000DatabaseWrapper
from django_pg8000.features import DatabaseFeatures as Pg8000DatabaseFeatures


class DatabaseFeatures(Pg8000DatabaseFeatures):
    # The underlying backend maps JSONField to PostgreSQL jsonb and adapts
    # database values through pg8000's JSON/JSONB converters. TIANA verifies
    # model-level JSONField writes and reads in its staging database health test.
    supports_json_field = True


class DatabaseWrapper(Pg8000DatabaseWrapper):
    features_class = DatabaseFeatures
