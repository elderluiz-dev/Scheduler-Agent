from __future__ import annotations

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main() -> None:
    credentials_path = Path("credentials.json")
    if not credentials_path.exists():
        raise SystemExit("Coloque o OAuth client do Google em credentials.json antes de rodar.")

    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    credentials = flow.run_local_server(port=0)
    Path("token.json").write_text(credentials.to_json(), encoding="utf-8")
    print("Token salvo em token.json")


if __name__ == "__main__":
    main()
