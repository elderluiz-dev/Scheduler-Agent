from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarClient:
    def __init__(self, token_file: str, calendar_id: str, resolve_calendar: bool = True) -> None:
        credentials = Credentials.from_authorized_user_file(token_file, SCOPES)
        self.service = build("calendar", "v3", credentials=credentials)
        self.calendar_id = self.resolve_calendar_id(calendar_id) if resolve_calendar else calendar_id

    @classmethod
    def from_token_json(
        cls,
        token_json: str,
        calendar_id: str,
        resolve_calendar: bool = True,
    ) -> "CalendarClient":
        token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
        with open(token_file, "w", encoding="utf-8") as handle:
            handle.write(token_json)
        return cls(token_file=token_file, calendar_id=calendar_id, resolve_calendar=resolve_calendar)

    def list_calendars(self) -> list[dict[str, Any]]:
        calendars: list[dict[str, Any]] = []
        page_token = None
        while True:
            response = self.service.calendarList().list(pageToken=page_token).execute()
            calendars.extend(response.get("items", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                return calendars

    def resolve_calendar_id(self, calendar_id_or_name: str) -> str:
        if calendar_id_or_name == "primary" or "@" in calendar_id_or_name:
            return calendar_id_or_name

        normalized_target = _normalize_calendar_name(calendar_id_or_name)
        calendars = self.list_calendars()
        for calendar in calendars:
            summary = _normalize_calendar_name(calendar.get("summary", ""))
            summary_override = _normalize_calendar_name(calendar.get("summaryOverride", ""))
            if normalized_target in {summary, summary_override}:
                return calendar["id"]

        available = ", ".join(
            calendar.get("summaryOverride") or calendar.get("summary", calendar.get("id", ""))
            for calendar in calendars
        )
        raise RuntimeError(
            f"Calendar '{calendar_id_or_name}' was not found. Available calendars: {available}"
        )

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


def _normalize_calendar_name(value: str) -> str:
    return value.casefold().strip()
