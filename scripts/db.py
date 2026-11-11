"""Schema tooling; application credentials intentionally cannot execute DDL."""
import argparse
import io
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from alembic import command
from alembic.config import Config
from sqlalchemy import URL, create_engine, inspect
import config  # noqa: F401 -- register models or load environment
import models  # noqa: F401 -- register models or load environment
from database.base import Base


def migration_engine():
    supplied = os.getenv("MIGRATION_DATABASE_URL")
    if supplied:
        return create_engine(supplied, hide_parameters=True)
    credentials = ROOT / ".local" / "mysql-admin.json"
    if not credentials.exists():
        raise SystemExit("Set MIGRATION_DATABASE_URL or run scripts/local_mysql.py setup.")
    password = json.loads(credentials.read_text())["password"]
    return create_engine(URL.create("mysql+pymysql", username="root", password=password,
                                   host="127.0.0.1", port=3307, database="jhy_development"), hide_parameters=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["migrate", "check", "status", "sql"])
    args = parser.parse_args()
    cfg = Config(str(ROOT / "alembic.ini"))
    if args.action == "sql":
        output = io.StringIO()
        cfg.output_buffer = output
        command.upgrade(cfg, "head", sql=True)
        destination = ROOT / "database" / "schema.sql"
        destination.write_text(output.getvalue(), encoding="utf-8")
        print("Wrote database/schema.sql")
        return
    engine = migration_engine()
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        if args.action == "migrate":
            tables = set(inspect(connection).get_table_names())
            if tables - {"alembic_version"} and "alembic_version" not in tables:
                raise SystemExit("Existing unversioned schema found. Review its schema before migration; no changes made.")
            command.upgrade(cfg, "head")
        elif args.action == "check":
            command.check(cfg)
        else:
            command.current(cfg)
            inspector = inspect(connection)
            print(f"Tables: {len(inspector.get_table_names())}; ORM models: {len(Base.metadata.tables)}")
    engine.dispose()


if __name__ == "__main__":
    main()
