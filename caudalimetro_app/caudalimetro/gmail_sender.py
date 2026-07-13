from __future__ import annotations

import base64
import threading
from email.message import EmailMessage
from pathlib import Path
from typing import Any


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

MODULE_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = MODULE_DIR / "credentials.json"
TOKEN_PATH = MODULE_DIR / "token.json"

_CREDENTIALS_LOCK = threading.Lock()


def _google_auth_classes() -> tuple[type[Any], type[Any], type[Any]]:
    """Load the optional Google dependencies only when email is sent."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError(
            "Dependências da Gmail API em falta. Instale "
            "google-api-python-client e google-auth-oauthlib."
        ) from exc

    return Request, Credentials, InstalledAppFlow


def _build_gmail_service(credentials: Any) -> Any:
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Dependência da Gmail API em falta. Instale google-api-python-client."
        ) from exc

    return build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )


def _write_token_atomically(credentials: Any, token_path: Path) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = token_path.with_name(f".{token_path.name}.tmp")
    temporary_path.write_text(credentials.to_json(), encoding="utf-8")
    temporary_path.replace(token_path)


def obter_credenciais(
    *,
    credentials_path: str | Path = CREDENTIALS_PATH,
    token_path: str | Path = TOKEN_PATH,
) -> Any:
    """Load, refresh or create the OAuth credentials used by the Gmail API."""
    credentials_file = Path(credentials_path)
    token_file = Path(token_path)
    Request, Credentials, InstalledAppFlow = _google_auth_classes()

    with _CREDENTIALS_LOCK:
        credentials = None

        if token_file.exists():
            try:
                credentials = Credentials.from_authorized_user_file(
                    token_file,
                    SCOPES,
                )
            except (OSError, ValueError):
                credentials = None

        if credentials and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not credentials_file.exists():
                raise FileNotFoundError(
                    f"Credenciais OAuth não encontradas: {credentials_file}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file,
                SCOPES,
            )
            credentials = flow.run_local_server(port=0)

        _write_token_atomically(credentials, token_file)
        return credentials


def send_gmail_message(
    message: EmailMessage,
    *,
    credentials_path: str | Path = CREDENTIALS_PATH,
    token_path: str | Path = TOKEN_PATH,
) -> str:
    """Send a complete MIME message through Gmail and return its message ID."""
    if not isinstance(message, EmailMessage):
        raise TypeError("A mensagem deve ser uma EmailMessage.")

    credentials = obter_credenciais(
        credentials_path=credentials_path,
        token_path=token_path,
    )
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    service = _build_gmail_service(credentials)
    result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body={"raw": raw_message},
        )
        .execute()
    )

    message_id = str(result.get("id") or "").strip() if isinstance(result, dict) else ""
    if not message_id:
        raise RuntimeError("A Gmail API não confirmou o envio da mensagem.")

    return message_id


__all__ = [
    "CREDENTIALS_PATH",
    "SCOPES",
    "TOKEN_PATH",
    "obter_credenciais",
    "send_gmail_message",
]
