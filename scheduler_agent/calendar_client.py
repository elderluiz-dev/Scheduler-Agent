from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarClient:
    def __init__(self, token_file: str, calendar_id: str) -> None:
        self.calendar_id = calendar_id
        credentials = Credentials.from_authorized_user_file(token_file, SCOPES)
        self.service = build("calendar", "v3", credentials=credentials)

    @classmethod
    def from_token_json(cls, token_json: str, calendar_id: str) -> "CalendarClient":
        token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
        with open(token_file, "w", encoding="utf-8") as handle:
            handle.write(token_json)
        return cls(token_file=token_file, calendar_id=calendar_id)

    def list_events(self, start: datetime, end: datetime, max_results: int = 100) -> list[dict[str, Any]]:
        response = (
            self.service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=max_results,
            )
            .execute()
        )
        return response.get("items", [])

    def list_daily_and_upcoming(
        self,
        day_start: datetime,
        lookahead_days: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        day_end = day_start + timedelta(days=1)
        month_end = day_start + timedelta(days=lookahead_days)
        today = self.list_events(day_start, day_end)
        upcoming = self.list_events(day_end, month_end)
        return today, upcoming

    def create_event(self, event: dict[str, Any]) -> dict[str, Any]:
        body = {
            "summary": event["summary"],
            "description": event.get("description", ""),
            "location": event.get("location", ""),
            "start": _event_time(event["start"], event.get("timezone")),
            "end": _event_time(event["end"], event.get("timezone")),
        }

        if event.get("attendees"):
            body["attendees"] = [{"email": email} for email in event["attendees"]]

        return (
            self.service.events()
            .insert(calendarId=self.calendar_id, body=body)
            .execute()
        )


def event_to_compact_dict(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": event.get("summary", "(sem titulo)"),
        "start": event.get("start", {}),
        "end": event.get("end", {}),
        "location": event.get("location", ""),
        "description": event.get("description", ""),
        "htmlLink": event.get("htmlLink", ""),
    }


def _event_time(value: str, timezone_name: str | None) -> dict[str, str]:
    if len(value) == 10:
        return {"date": value}
    payload = {"dateTime": value}
    if timezone_name:
        payload["timeZone"] = timezone_name
    return payload


def dump_event_json(event: dict[str, Any]) -> str:
    return json.dumps(event, ensure_ascii=True, indent=2)
