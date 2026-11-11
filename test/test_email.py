"""Check the backend's Gmail SMTP login without sending a message."""

import os
import smtplib
import ssl
from pathlib import Path

from dotenv import load_dotenv


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    local_env = root / ".env.local"
    default_env = local_env if local_env.is_file() else root / ".env"
    env_file = Path(os.getenv("JHY_ENV_FILE", str(default_env)))
    load_dotenv(env_file)

    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD", "")
    if not sender or len(password) != 16 or any(char.isspace() for char in password):
        print(f"{env_file.name}에서 Gmail 주소와 공백 없는 16자 앱 비밀번호를 확인해 주세요.")
        return 2

    phase = "TLS 연결"
    try:
        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=10)
        try:
            phase = "SMTP 인증"
            smtp.login(sender, password)
        finally:
            smtp.close()
    except smtplib.SMTPResponseException as error:
        print(f"{phase} 실패 (SMTP {error.smtp_code})")
        return 1
    except (OSError, smtplib.SMTPException) as error:
        print(f"{phase} 실패 ({type(error).__name__})")
        return 1

    print("SMTP 인증 성공")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
