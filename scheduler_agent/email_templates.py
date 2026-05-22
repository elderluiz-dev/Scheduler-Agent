from __future__ import annotations

import html
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


def render_daily_summary_email(
    intro_text: str,
    today_events: list[dict[str, Any]],
    upcoming_events: list[dict[str, Any]],
    now: datetime,
    timezone_name: str,
    calendar_label: str,
) -> str:
    today_cards = _render_event_list(today_events, timezone_name, empty_text="Hoje nao ha eventos no calendario 1ads.")
    upcoming_cards = _render_event_list(
        upcoming_events,
        timezone_name,
        empty_text="Nao encontrei proximos eventos no periodo configurado.",
        compact=True,
    )

    return f"""<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;color:#1f2937;">
    <div style="display:none;max-height:0;overflow:hidden;">Programacao academica de {now:%d/%m/%Y}</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f7fb;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;background:#ffffff;border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;">
            <tr>
              <td style="background:#12355b;padding:26px 28px;color:#ffffff;">
                <div style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;opacity:.78;">Planner academico</div>
                <h1 style="margin:8px 0 0;font-size:26px;line-height:1.2;font-weight:700;">Programacao do dia</h1>
                <p style="margin:8px 0 0;font-size:15px;opacity:.88;">{now:%d/%m/%Y} · {html.escape(calendar_label)}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 8px;">
                <p style="margin:0;color:#374151;font-size:15px;line-height:1.55;">{html.escape(intro_text)}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 28px 4px;">
                <h2 style="margin:0 0 12px;font-size:18px;color:#111827;">Hoje</h2>
                {today_cards}
              </td>
            </tr>
            <tr>
              <td style="padding:18px 28px 22px;">
                <h2 style="margin:0 0 12px;font-size:18px;color:#111827;">Proximos eventos</h2>
                {upcoming_cards}
              </td>
            </tr>
            <tr>
              <td style="padding:18px 28px;background:#f9fafb;border-top:1px solid #e5e7eb;color:#6b7280;font-size:13px;line-height:1.5;">
                Enviado automaticamente as 06:30. Revise os horarios no Google Calendar antes de compromissos importantes.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _render_event_list(
    events: list[dict[str, Any]],
    timezone_name: str,
    empty_text: str,
    compact: bool = False,
) -> str:
    if not events:
        return f"""
        <div style="border:1px dashed #cbd5e1;border-radius:10px;padding:16px;background:#f8fafc;color:#64748b;font-size:14px;">
          {html.escape(empty_text)}
        </div>"""

    return "\n".join(_render_event_card(event, timezone_name, compact) for event in events)


def _render_event_card(event: dict[str, Any], timezone_name: str, compact: bool) -> str:
    title = html.escape(event.get("summary") or "(sem titulo)")
    location = html.escape(event.get("location") or "")
    description = html.escape((event.get("description") or "").strip())
    link = html.escape(event.get("htmlLink") or "")
    when = html.escape(_format_event_time(event, timezone_name))
    padding = "12px 14px" if compact else "14px 16px"

    location_html = (
        f'<div style="margin-top:6px;color:#64748b;font-size:13px;">Local: {location}</div>'
        if location
        else ""
    )
    description_html = (
        f'<div style="margin-top:8px;color:#4b5563;font-size:13px;line-height:1.45;">{description}</div>'
        if description and not compact
        else ""
    )
    link_html = (
        f'<a href="{link}" style="display:inline-block;margin-top:10px;color:#0f766e;text-decoration:none;font-size:13px;font-weight:700;">Abrir no Calendar</a>'
        if link
        else ""
    )

    return f"""
    <div style="border:1px solid #e5e7eb;border-left:4px solid #0f766e;border-radius:10px;padding:{padding};margin-bottom:10px;background:#ffffff;">
      <div style="font-size:13px;color:#0f766e;font-weight:700;margin-bottom:5px;">{when}</div>
      <div style="font-size:16px;color:#111827;font-weight:700;line-height:1.35;">{title}</div>
      {location_html}
      {description_html}
      {link_html}
    </div>"""


def _format_event_time(event: dict[str, Any], timezone_name: str) -> str:
    start = event.get("start", {})
    end = event.get("end", {})
    if start.get("date"):
        start_date = datetime.fromisoformat(start["date"])
        return start_date.strftime("%d/%m") + " · dia inteiro"

    timezone = ZoneInfo(timezone_name)
    start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00")).astimezone(timezone)
    end_value = end.get("dateTime")
    if not end_value:
        return start_dt.strftime("%d/%m · %H:%M")
    end_dt = datetime.fromisoformat(end_value.replace("Z", "+00:00")).astimezone(timezone)
    if start_dt.date() == end_dt.date():
        return f"{start_dt:%d/%m · %H:%M} - {end_dt:%H:%M}"
    return f"{start_dt:%d/%m %H:%M} - {end_dt:%d/%m %H:%M}"
