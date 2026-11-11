"""Manage only this workspace's private, loopback-only MySQL instance."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import socket
import subprocess
import time
import urllib.request
import zipfile

import pymysql
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
VERSION = "8.4.13"
ARCHIVE = f"mysql-{VERSION}-winx64"
EXPECTED_SHA256 = "e9cd98b1d23f122987b1afca26ad942efec5891481103d48ae3cde237fa3ea54"
SERVER = LOCAL / "mysql-dist" / ARCHIVE
DATA = LOCAL / "mysql-data"
INI = LOCAL / "my.ini"
ADMIN = LOCAL / "mysql-admin.json"
PORT = 3307


def connection():
    credentials = json.loads(ADMIN.read_text())
    return pymysql.connect(host="127.0.0.1", port=PORT, user="root", password=credentials["password"], autocommit=True)


def start():
    if not INI.exists():
        raise SystemExit("Run setup first.")
    try:
        with connection() as db:
            with db.cursor() as cursor:
                cursor.execute("SELECT @@datadir")
                actual = Path(cursor.fetchone()[0]).resolve()
                if actual != DATA.resolve():
                    raise SystemExit("Port belongs to a different MySQL instance; no action taken.")
        print("Workspace MySQL already running on 127.0.0.1:3307")
        return
    except pymysql.OperationalError:
        pass
    arguments = [str(SERVER / "bin" / "mysqld.exe"), f"--defaults-file={INI}"]
    init_sql = LOCAL / "mysql-init.sql"
    if init_sql.exists():
        arguments.append(f"--init-file={init_sql}")
    log = (LOCAL / "mysql-process.log").open("ab")
    process = subprocess.Popen(arguments, stdout=log, stderr=log,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    (LOCAL / "mysql.pid").write_text(str(process.pid))
    for _ in range(120):
        if process.poll() is not None:
            raise SystemExit("MySQL failed to start; inspect .local/mysql-error.log locally.")
        try:
            with connection():
                break
        except pymysql.OperationalError:
            time.sleep(0.5)
    else:
        raise SystemExit("MySQL startup timed out.")
    init_sql.unlink(missing_ok=True)
    print("Workspace MySQL running on 127.0.0.1:3307")


def setup():
    LOCAL.mkdir(exist_ok=True)
    if DATA.exists() and any(DATA.iterdir()):
        if not ADMIN.exists() or not INI.exists():
            raise SystemExit("Existing data found; initialization refused to preserve data.")
        start()
        return
    if (ROOT / ".env.local").exists() or ADMIN.exists():
        raise SystemExit("Existing local credentials found without a complete data directory; setup refused to preserve configuration.")
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", PORT)) == 0:
            raise SystemExit("Port 3307 is occupied; no existing service was changed.")
    if not SERVER.exists():
        archive_path = LOCAL / "downloads" / f"{ARCHIVE}.zip"
        archive_path.parent.mkdir(exist_ok=True)
        if not archive_path.exists():
            urllib.request.urlretrieve(f"https://cdn.mysql.com/Downloads/MySQL-8.4/{ARCHIVE}.zip", archive_path)
        if hashlib.file_digest(archive_path.open("rb"), "sha256").hexdigest() != EXPECTED_SHA256:
            raise SystemExit("Official archive checksum mismatch.")
        destination = LOCAL / "mysql-dist"
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                if not (destination / member.filename).resolve().is_relative_to(destination.resolve()):
                    raise SystemExit("Unsafe archive path.")
            archive.extractall(destination)
    DATA.mkdir(exist_ok=True)
    settings = (
        f"[mysqld]\nbasedir={SERVER.as_posix()}\ndatadir={DATA.as_posix()}\nport={PORT}\n"
        f"bind-address=127.0.0.1\nmysqlx=0\nlog-error={(LOCAL / 'mysql-error.log').as_posix()}\n"
        "character-set-server=utf8mb4\ncollation-server=utf8mb4_0900_ai_ci\n"
        "default-time-zone=+00:00\nlower-case-table-names=1\n"
    )
    INI.write_text(settings, encoding="utf-8")
    # Initialization does not start a network listener. Credentials are set by
    # init-file before the first server accepts connections.
    result = subprocess.run([str(SERVER / "bin" / "mysqld.exe"), f"--defaults-file={INI}", "--initialize-insecure"],
                            capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode:
        raise SystemExit("Initialization failed; existing data was not removed. Inspect .local/mysql-error.log.")
    root_password, app_password, test_password = (secrets.token_urlsafe(32) for _ in range(3))
    ADMIN.write_text(json.dumps({"password": root_password}), encoding="utf-8")
    (LOCAL / "mysql-init.sql").write_text(
        f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{root_password}';\n"
        "CREATE DATABASE jhy_development CHARACTER SET utf8mb4;\n"
        "CREATE DATABASE jhy_test CHARACTER SET utf8mb4;\n"
        f"CREATE USER 'jhy_app'@'localhost' IDENTIFIED BY '{app_password}';\n"
        f"CREATE USER 'jhy_test'@'localhost' IDENTIFIED BY '{test_password}';\n"
        "GRANT SELECT, INSERT, UPDATE, DELETE ON jhy_development.* TO 'jhy_app'@'localhost';\n"
        "GRANT ALL ON jhy_test.* TO 'jhy_test'@'localhost';\n", encoding="utf-8")
    env = ROOT / ".env.local"
    if env.exists():
        raise SystemExit(".env.local already exists; not overwritten. Complete local setup manually.")
    existing = dotenv_values(ROOT / ".env")
    values = {
        "DB_HOST": "127.0.0.1", "DB_PORT": str(PORT), "DB_USER": "jhy_app",
        "DB_PASSWORD": app_password, "DB_NAME": "jhy_development",
        "EMAIL_CODE_SECRET": secrets.token_urlsafe(32), "ADMIN_EMAILS": "",
        "COOKIE_SECURE": "false", "WORKER_ENABLED": "true",
        "ESTIMATED_CYCLE_SECONDS": "2400",
    }
    for name in ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"):
        values[name] = existing.get(name) or ""
    # JSON quoted strings are valid dotenv values for these generated credentials.
    env.write_text("\n".join(f"{key}={json.dumps(value)}" for key, value in values.items()) + "\n", encoding="utf-8")
    (LOCAL / "test-database.env").write_text(
        f"TEST_DATABASE_URL=mysql+pymysql://jhy_test:{test_password}@127.0.0.1:{PORT}/jhy_test\n", encoding="utf-8")
    start()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["setup", "start", "stop", "status"])
    args = parser.parse_args()
    if args.action == "setup":
        setup()
    elif args.action == "start":
        start()
    elif args.action == "status":
        with connection() as db:
            with db.cursor() as cursor:
                cursor.execute("SELECT VERSION(), @@port, @@datadir")
                version, port, data = cursor.fetchone()
                print(f"MySQL {version}; 127.0.0.1:{port}; workspace data: {Path(data).resolve() == DATA.resolve()}")
    else:
        with connection() as db:
            with db.cursor() as cursor:
                cursor.execute("SELECT @@datadir")
                if Path(cursor.fetchone()[0]).resolve() != DATA.resolve():
                    raise SystemExit("Refusing to stop a different MySQL instance.")
                cursor.execute("SHUTDOWN")
        print("Workspace MySQL stopped; data preserved.")


if __name__ == "__main__":
    main()
