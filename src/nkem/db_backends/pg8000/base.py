"""TIANA's Django adapter for pg8000 with Hyperdrive-safe transaction control.

Hyperdrive uses transaction pooling. pg8000.native.Connection.run() sends
extended-protocol unnamed statements, even for some parameter-free control
commands. Those unnamed statements can be lost when Hyperdrive returns a
backend connection between protocol Sync points.

Keep transaction-control and session-setup statements on PostgreSQL's simple
query protocol. Django-pg8000 already composes ORM parameters client-side and
executes ordinary ORM statements through execute_simple().
"""
from django.conf import settings

from django_pg8000 import base as pg8000_base
from django_pg8000.base import (
    DatabaseConnection as Pg8000DatabaseConnection,
    DatabaseWrapper as Pg8000DatabaseWrapper,
)
from django_pg8000.features import DatabaseFeatures as Pg8000DatabaseFeatures
from django_pg8000.operations import DatabaseOperations


class HyperdriveDatabaseConnection(Pg8000DatabaseConnection):
    """Use simple-query protocol for unparameterized transaction commands."""

    def _run(self, sql, params=(), stream=None):
        if not params and stream is None:
            return self._con.execute_simple(sql)
        return super()._run(sql, params=params, stream=stream)

    def commit(self):
        # COMMIT/ROLLBACK must use the same simple protocol as START TRANSACTION.
        return self._con.execute_simple("COMMIT")

    def rollback(self):
        return self._con.execute_simple("ROLLBACK")


class DatabaseFeatures(Pg8000DatabaseFeatures):
    # TIANA's model-level JSONField round-trip is covered by /health/.
    supports_json_field = True


class DatabaseWrapper(Pg8000DatabaseWrapper):
    features_class = DatabaseFeatures

    def get_new_connection(self, conn_params):
        return HyperdriveDatabaseConnection(conn_params)

    def ensure_timezone(self):
        if self.connection is None:
            return False

        conn_timezone_name = self.connection.info.get_parameter_status("TimeZone")
        timezone_name = settings.TIME_ZONE
        if settings.USE_TZ:
            tzname = timezone_name
            timestamptz_in = pg8000_base.timestamptz_in_use_tz
        else:
            tzname = "UTC"
            timestamptz_in = pg8000_base.timestamptz_in_no_tz

        self.connection._con.register_in_adapter(pg8000_base.TIMESTAMPTZ, timestamptz_in)
        self.connection._con.register_in_adapter(
            pg8000_base.TIMESTAMPTZ_ARRAY,
            pg8000_base.timestamptz_array_in,
        )

        if tzname and conn_timezone_name != tzname:
            sql = f"SET TIMEZONE TO {DatabaseOperations._literal(tzname)}"
            self.connection._execute_simple(sql)
            return True
        return False

    def ensure_role(self):
        if self.connection is None:
            return False
        new_role = self.settings_dict.get("OPTIONS", {}).get("assume_role")
        if new_role:
            sql = self.ops.compose_sql("SET ROLE %s", [new_role])
            self.connection._execute_simple(sql)
            return True
        return False
