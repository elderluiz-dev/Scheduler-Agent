# Scheduler Agent

Agente de rotina em Python usando Gemini GenAI, Google Calendar e envio por SMTP.

Ele roda sem interface:

- envia um resumo diario por email com a programacao do dia e os proximos eventos do mes;
- le eventos existentes do Google Calendar;
- interpreta pedidos em linguagem natural para criar eventos;
- pede confirmacao antes de adicionar um evento ao calendario.

## Configuracao local

1. Crie e ative um ambiente Python.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copie `.env.example` para `.env` e preencha:

```powershell
Copy-Item .env.example .env
```

3. No Google Cloud Console, crie um OAuth Client do tipo "Desktop app" e baixe o arquivo como `credentials.json`.

4. Gere o token do Google Calendar:

```powershell
python scripts/auth_google.py
```

Isso cria `token.json`. Ele permite que o agente acesse seu Google Calendar.

5. Teste o resumo diario:

```powershell
python -m scheduler_agent daily-summary --send-email
```

## Criar eventos com confirmacao

Para pedir um novo evento:

```powershell
python -m scheduler_agent propose-event "Adicionar prova de Calculo dia 12 de junho as 10h"
```

O agente retorna um JSON com os detalhes normalizados. Depois de revisar:

```powershell
python -m scheduler_agent add-event --event-json proposed_event.json
```

Tambem e possivel passar o JSON inline:

```powershell
python -m scheduler_agent add-event --event-json '{"summary":"Prova de Calculo","start":"2026-06-12T10:00:00-03:00","end":"2026-06-12T11:00:00-03:00"}'
```

## Fazer perguntas ao planner

```powershell
python -m scheduler_agent ask "Quais sao minhas provas nas proximas semanas?" --send-email
```

No GitHub Actions, use o workflow `Calendar Question` para fazer uma pergunta manualmente e receber a resposta por email.

## GitHub Actions

Configure estes secrets no repositorio:

- `GEMINI_API_KEY`
- `GOOGLE_TOKEN_JSON`: conteudo inteiro do seu `token.json`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO`

Opcional:

- `GOOGLE_CALENDAR_ID`
- `GEMINI_MODEL`

O workflow `.github/workflows/daily-summary.yml` roda todos os dias as 06:30 no horario de Brasilia.

O workflow `.github/workflows/calendar-event.yml` permite criar evento manualmente pelo GitHub Actions.

1. Rode com `confirm=false` e preencha `request`.
2. Voce recebera a proposta em JSON por email.
3. Rode novamente com `confirm=true`, cole o JSON revisado em `event_json` e deixe `request` vazio.
