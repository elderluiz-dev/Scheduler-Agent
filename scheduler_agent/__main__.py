from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from scheduler_agent.calendar_client import CalendarClient, dump_event_json
from scheduler_agent.config import load_settings
from scheduler_agent.emailer import send_email
from scheduler_agent.gemini_agent import GeminiPlanner


def main() -> None:
    parser = argparse.ArgumentParser(description="Scheduler Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily = subparsers.add_parser("daily-summary", help="Gera resumo diario")
    daily.add_argument("--send-email", action="store_true")

    propose = subparsers.add_parser("propose-event", help="Interpreta pedido de novo evento")
    propose.add_argument("request")
    propose.add_argument("--send-email", action="store_true")

    ask = subparsers.add_parser("ask", help="Responde perguntas usando eventos do calendario")
    ask.add_argument("question")
    ask.add_argument("--send-email", action="store_true")

    add = subparsers.add_parser("add-event", help="Adiciona evento confirmado ao calendario")
    add.add_argument("--event-json", required=True, help="JSON inline ou caminho para arquivo JSON")
    add.add_argument("--send-email", action="store_true")

    args = parser.parse_args()
    settings = load_settings()
    timezone = ZoneInfo(settings.timezone)
    now = datetime.now(timezone)

    token_json = os.getenv("GOOGLE_TOKEN_JSON")
    calendar = (
        CalendarClient.from_token_json(token_json, settings.google_calendar_id)
        if token_json
        else CalendarClient(settings.google_token_file, settings.google_calendar_id)
    )
    planner = GeminiPlanner(settings.gemini_api_key, settings.gemini_model)

    if args.command == "daily-summary":
        day_start = datetime.combine(now.date(), time.min, tzinfo=timezone)
        today, upcoming = calendar.list_daily_and_upcoming(day_start, settings.daily_lookahead_days)
        body = planner.daily_summary(today, upcoming, now)
        print(body)
        if args.send_email:
            _send_configured_email(
                settings,
                f"Programacao do dia - {now:%d/%m/%Y}",
                body,
            )
        return

    if args.command == "ask":
        start = datetime.combine(now.date(), time.min, tzinfo=timezone)
        end = start + timedelta(days=settings.daily_lookahead_days)
        events = calendar.list_events(start, end)
        body = planner.answer_question(args.question, events, now)
        print(body)
        if args.send_email:
            _send_configured_email(
                settings,
                "Resposta do planner",
                body,
            )
        return

    if args.command == "propose-event":
        event = planner.propose_event(args.request, now, settings.timezone)
        body = dump_event_json(event)
        print(body)
        if args.send_email:
            _send_configured_email(
                settings,
                "Confirmacao de novo evento",
                "Revise o evento abaixo. Se estiver correto, rode o workflow com confirm=true.\n\n" + body,
            )
        return

    if args.command == "add-event":
        event = _load_event_json(args.event_json)
        if event.get("needs_clarification"):
            raise RuntimeError(f"Evento ainda precisa de esclarecimento: {event.get('clarification_question')}")
        created = calendar.create_event(event)
        body = "Evento criado com sucesso:\n\n" + dump_event_json(created)
        print(body)
        if args.send_email:
            _send_configured_email(
                settings,
                "Evento adicionado ao calendario",
                body,
            )


def _load_event_json(value: str) -> dict:
    path = Path(value)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def _send_configured_email(settings, subject: str, body: str) -> None:
    required = {
        "SMTP_HOST": settings.smtp_host,
        "SMTP_USERNAME": settings.smtp_username,
        "SMTP_PASSWORD": settings.smtp_password,
        "EMAIL_FROM": settings.email_from,
        "EMAIL_TO": settings.email_to,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError("Missing email settings: " + ", ".join(missing))

    send_email(
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_username,
        settings.smtp_password,
        settings.email_from,
        settings.email_to,
        subject,
        body,
    )


if __name__ == "__main__":
    main()
