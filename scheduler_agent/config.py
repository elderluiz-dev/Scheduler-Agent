from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    google_calendar_id: str
    google_token_file: str
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    email_from: str | None
    email_to: str | None
    timezone: str
    daily_lookahead_days: int


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        gemini_api_key=_required("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        google_calendar_id=os.getenv("GOOGLE_CALENDAR_ID", "primary"),
        google_token_file=os.getenv("GOOGLE_TOKEN_FILE", "token.json"),
        smtp_host=os.getenv("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        email_from=os.getenv("EMAIL_FROM"),
        email_to=os.getenv("EMAIL_TO"),
        timezone=os.getenv("TIMEZONE", "America/Sao_Paulo"),
        daily_lookahead_days=int(os.getenv("DAILY_LOOKAHEAD_DAYS", "31")),
    )


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
