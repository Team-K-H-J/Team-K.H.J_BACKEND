"""Local administration without embedding passwords or device keys in source."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("JHY_ENV_FILE", str(ROOT / ".env.local") if (ROOT / ".env.local").exists() else str(ROOT / ".env"))

from sqlalchemy import select
from database.connection import SessionLocal
from models.devices import Devices
from models.operations import Device_Credential, Device_Runtime
from models.state import State
from models.users import Users
from services.common import utcnow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    device = commands.add_parser("add-device")
    device.add_argument("device_id")
    device.add_argument("name")
    device.add_argument("--expected-seconds", type=int, default=None)
    administrator = commands.add_parser("grant-admin")
    administrator.add_argument("email")
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.action == "add-device":
            if not 1 <= len(args.device_id) <= 24 or not 1 <= len(args.name.strip()) <= 24:
                raise SystemExit("Device ID and name must contain 1-24 characters.")
            if db.get(Devices, args.device_id) or db.scalar(select(Devices).where(Devices.device_name == args.name)):
                raise SystemExit("Device already exists. No existing device or key was changed.")
            key = secrets.token_urlsafe(32)
            expected_seconds = args.expected_seconds or int(os.getenv("ESTIMATED_CYCLE_SECONDS", "2400"))
            if expected_seconds < 1:
                raise SystemExit("Expected duration must be positive.")
            db.add(Devices(device_id=args.device_id, device_name=args.name))
            db.flush()
            db.add_all([Device_Credential(device_id=args.device_id, key_hash=hashlib.sha256(key.encode()).hexdigest()),
                        Device_Runtime(device_id=args.device_id, cycle_status="not_used", expected_seconds=expected_seconds),
                        State(device_id=args.device_id, state="not_used", updated_at=utcnow())])
            key_file = ROOT / ".local" / "device-keys.json"
            key_file.parent.mkdir(exist_ok=True)
            keys = json.loads(key_file.read_text(encoding="utf-8")) if key_file.exists() else {}
            keys[args.device_id] = key
            key_file.write_text(json.dumps(keys, indent=2), encoding="utf-8")
            db.commit()
            print("Device registered. Its credential is in .local/device-keys.json (excluded from Git).")
        else:
            email = args.email.lower()
            if db.scalar(select(Users).where(Users.email == email)) is None:
                raise SystemExit("A verified, registered account is required before granting admin access.")
            env_file = Path(os.environ["JHY_ENV_FILE"])
            lines = env_file.read_text(encoding="utf-8").splitlines()
            existing = {item.strip() for item in os.getenv("ADMIN_EMAILS", "").split(",") if item.strip()}
            existing.add(email)
            lines = [line for line in lines if not line.startswith("ADMIN_EMAILS=")]
            lines.append("ADMIN_EMAILS=" + json.dumps(",".join(sorted(existing))))
            env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print("Administrator allowlist updated. Restart the API to load the configuration.")


if __name__ == "__main__":
    main()
