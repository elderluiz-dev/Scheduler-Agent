from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from google import genai

from scheduler_agent.calendar_client import event_to_compact_dict


class GeminiPlanner:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def daily_summary(
        self,
        today_events: list[dict[str, Any]],
        upcoming_events: list[dict[str, Any]],
        now: datetime,
    ) -> str:
        prompt = f"""
Voce e uma IA planner para faculdade. Escreva um email curto, claro e util em portugues do Brasil.

Contexto:
- Agora: {now.isoformat()}
- O usuario quer a programacao do dia em ordem cronologica.
- Depois, liste os proximos eventos do mes tambem em ordem cronologica.
- Foque em provas, trabalhos, entregas, aulas, compromissos e prazos.
- Nao invente eventos. Se nao houver eventos, diga isso de forma objetiva.
- Termine com uma frase curta de planejamento do dia.

Eventos de hoje:
{json.dumps([event_to_compact_dict(event) for event in today_events], ensure_ascii=False, indent=2)}

Proximos eventos:
{json.dumps([event_to_compact_dict(event) for event in upcoming_events], ensure_ascii=False, indent=2)}
"""
        return self._text(prompt)

    def answer_question(
        self,
        question: str,
        events: list[dict[str, Any]],
        now: datetime,
    ) -> str:
        prompt = f"""
Voce e uma IA planner para faculdade. Responda em portugues do Brasil usando somente os eventos fornecidos.

Contexto:
- Agora: {now.isoformat()}
- Seja direto e organizado.
- Se a resposta depender de algo que nao esta nos eventos, diga que nao encontrou essa informacao no calendario.
- Quando citar eventos, preserve ordem cronologica quando fizer sentido.

Pergunta:
{question}

Eventos disponiveis:
{json.dumps([event_to_compact_dict(event) for event in events], ensure_ascii=False, indent=2)}
"""
        return self._text(prompt)

    def propose_event(self, request: str, now: datetime, timezone_name: str) -> dict[str, Any]:
        prompt = f"""
Extraia um evento de calendario a partir do pedido do usuario.

Responda somente com JSON valido, sem markdown.

Regras:
- Agora: {now.isoformat()}
- Timezone padrao: {timezone_name}
- Use ISO 8601 para start e end.
- Se o usuario nao disser duracao, use 1 hora.
- Se for evento de dia inteiro, use YYYY-MM-DD em start e end, com end exclusivo.
- summary deve ser curto.
- description deve preservar detalhes uteis do pedido.
- Se faltar data ou horario essencial, retorne needs_clarification=true e uma pergunta em clarification_question.
- Nao crie no calendario; apenas proponha.

Formato:
{{
  "needs_clarification": false,
  "clarification_question": "",
  "summary": "",
  "description": "",
  "location": "",
  "start": "",
  "end": "",
  "timezone": "{timezone_name}",
  "attendees": []
}}

Pedido do usuario:
{request}
"""
        response = self._text(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Gemini returned invalid JSON: {response}") from exc

    def _text(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty response")
        return response.text.strip()
