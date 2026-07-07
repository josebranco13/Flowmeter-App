from __future__ import annotations

import json
import mimetypes
import os
import smtplib
import ssl
import threading
import webbrowser
from datetime import datetime
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path
from typing import Any, Callable, Iterable

from .config import BASE_DIR, MAIL_DRAFTS_DIR, PDF_EXPORTS_DIR


DEFAULT_CONFIG_PATH = BASE_DIR / "data" / "email_config.json"


# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

def load_email_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro de configuração de email não encontrado: {path}")

    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise RuntimeError("Configuração de email inválida.")

    return config


def _resolve_app_path(path: str | Path) -> Path:
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved
    return BASE_DIR / resolved


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


# ---------------------------------------------------------------------------
# Seleção dos anexos
# ---------------------------------------------------------------------------

def get_related_json_path(pdf_path: str | Path) -> Path | None:
    pdf_path = Path(pdf_path)
    json_path = pdf_path.with_suffix(".json")
    if json_path.exists() and json_path.is_file():
        return json_path
    return None


def get_files_for_selected_pdf(
    pdf_path: str | Path,
    json_path: str | Path | None = None,
    *,
    require_pdf_and_json: bool = True,
) -> list[Path]:
    pdf = Path(pdf_path)
    if not pdf.exists() or not pdf.is_file():
        raise FileNotFoundError(f"PDF não encontrado: {pdf}")

    if json_path is None:
        manifest = get_related_json_path(pdf)
    else:
        manifest = Path(json_path)

    if require_pdf_and_json and (manifest is None or not manifest.exists() or not manifest.is_file()):
        raise FileNotFoundError(f"JSON respetivo em falta para o PDF: {pdf.name}")

    files = [pdf]
    if manifest is not None and manifest.exists() and manifest.is_file():
        files.append(manifest)

    return files


def get_files_for_all_exports(config: dict[str, Any]) -> list[Path]:
    exports_config = config.get("exports", {})
    automatic_config = config.get("automatic_send", {})
    export_dir = _resolve_app_path(exports_config.get("directory", "data/pdf_exportados"))
    include_json = bool(exports_config.get("include_json", True))
    require_pdf_and_json = bool(
        automatic_config.get(
            "require_pdf_and_json",
            exports_config.get("require_pdf_and_json", True),
        )
    )

    if not export_dir.exists():
        return []

    files: list[Path] = []
    seen: set[Path] = set()

    for pdf_path in sorted(export_dir.glob("*.pdf")):
        json_path = get_related_json_path(pdf_path)

        if require_pdf_and_json and json_path is None:
            continue

        if pdf_path not in seen:
            files.append(pdf_path)
            seen.add(pdf_path)

        if include_json and json_path is not None and json_path not in seen:
            files.append(json_path)
            seen.add(json_path)

    return files


def count_pdf_json_pairs(config: dict[str, Any]) -> int:
    exports_config = config.get("exports", {})
    export_dir = _resolve_app_path(exports_config.get("directory", "data/pdf_exportados"))
    if not export_dir.exists():
        return 0
    return sum(1 for pdf_path in export_dir.glob("*.pdf") if get_related_json_path(pdf_path))


def has_exported_pdf_json_pairs(config: dict[str, Any]) -> bool:
    return count_pdf_json_pairs(config) > 0


# ---------------------------------------------------------------------------
# Envio real por SMTP
# ---------------------------------------------------------------------------

def send_email_with_attachments(
    *,
    config: dict[str, Any],
    attachments: list[Path],
    subject: str,
    body: str,
) -> None:
    if not config.get("enabled", False):
        raise RuntimeError("O envio de email está desativado na configuração.")

    if not attachments:
        raise RuntimeError("Não existem ficheiros para enviar.")

    for attachment in attachments:
        if not attachment.exists() or not attachment.is_file():
            raise FileNotFoundError(f"Ficheiro em falta: {attachment.name}")

    smtp_config = config.get("smtp", {})
    account = config.get("account", {})
    recipients = config.get("recipients", {})

    sender_name = str(account.get("sender_name") or "").strip()
    sender_email = str(account.get("sender_email") or "").strip()
    username = str(account.get("username") or sender_email).strip()
    password_env = str(account.get("password_env") or "").strip()

    if not sender_email or not username or not password_env:
        raise RuntimeError("Configuração da conta de email incompleta.")

    password = os.environ.get(password_env)
    if not password:
        raise RuntimeError(f"Variável de ambiente em falta: {password_env}")

    to_recipients = _as_list(recipients.get("to"))
    cc_recipients = _as_list(recipients.get("cc"))
    bcc_recipients = _as_list(recipients.get("bcc"))
    all_recipients = to_recipients + cc_recipients + bcc_recipients

    if not all_recipients:
        raise RuntimeError("Não existem destinatários configurados.")

    message = EmailMessage()
    if sender_name:
        message["From"] = f"{sender_name} <{sender_email}>"
    else:
        message["From"] = sender_email
    message["To"] = ", ".join(to_recipients)
    if cc_recipients:
        message["Cc"] = ", ".join(cc_recipients)
    message["Subject"] = subject
    message.set_content(body)

    for file_path in attachments:
        content_type, encoding = mimetypes.guess_type(file_path.name)
        if content_type is None or encoding is not None:
            maintype, subtype = "application", "octet-stream"
        else:
            maintype, subtype = content_type.split("/", 1)

        message.add_attachment(
            file_path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=file_path.name,
        )

    host = str(smtp_config.get("host") or "").strip()
    port = int(smtp_config.get("port") or 587)
    security = str(smtp_config.get("security") or "starttls").lower().strip()
    timeout = int(smtp_config.get("timeout_seconds") or 20)
    ssl_context = ssl.create_default_context()

    if security == "ssl":
        with smtplib.SMTP_SSL(host, port, timeout=timeout, context=ssl_context) as server:
            server.login(username, password)
            server.send_message(message, from_addr=sender_email, to_addrs=all_recipients)
        return

    with smtplib.SMTP(host, port, timeout=timeout) as server:
        server.ehlo()
        if security == "starttls":
            server.starttls(context=ssl_context)
            server.ehlo()
        server.login(username, password)
        server.send_message(message, from_addr=sender_email, to_addrs=all_recipients)


def send_selected_export_email(
    *,
    config: dict[str, Any],
    pdf_path: str | Path,
    json_path: str | Path | None = None,
    molde: str = "-",
) -> None:
    exports_config = config.get("exports", {})
    automatic_config = config.get("automatic_send", {})
    require_pdf_and_json = bool(
        automatic_config.get(
            "require_pdf_and_json",
            exports_config.get("require_pdf_and_json", True),
        )
    )

    attachments = get_files_for_selected_pdf(
        pdf_path,
        json_path,
        require_pdf_and_json=require_pdf_and_json,
    )

    pdf = Path(pdf_path)
    manifest = Path(json_path) if json_path is not None else get_related_json_path(pdf)

    message_config = config.get("messages", {}).get("single", {})
    context = {
        "molde": molde,
        "pdf_nome": pdf.name,
        "json_nome": manifest.name if manifest is not None else "-",
        "total_ficheiros": len(attachments),
    }
    subject = str(message_config.get("subject") or "Registo de caudais - Molde {molde}").format(**context)
    body = str(message_config.get("body") or "Segue em anexo o registo de caudais.").format(**context)

    send_email_with_attachments(
        config=config,
        attachments=attachments,
        subject=subject,
        body=body,
    )


def send_all_exports_email(*, config: dict[str, Any]) -> None:
    attachments = get_files_for_all_exports(config)
    if not attachments:
        raise RuntimeError("Não existem pares PDF/JSON exportados para enviar.")

    message_config = config.get("messages", {}).get("all", {})
    context = {
        "total_ficheiros": len(attachments),
        "total_pares": count_pdf_json_pairs(config),
    }
    subject = str(message_config.get("subject") or "Registos de caudais exportados").format(**context)
    body = str(message_config.get("body") or "Seguem em anexo os registos de caudais exportados.").format(**context)

    send_email_with_attachments(
        config=config,
        attachments=attachments,
        subject=subject,
        body=body,
    )


def _run_async(
    callback: Callable[[], None],
    on_result: Callable[[bool, str], None] | None = None,
) -> threading.Thread:
    def worker() -> None:
        try:
            callback()
        except Exception as exc:
            if on_result:
                on_result(False, str(exc))
            return
        if on_result:
            on_result(True, "Email enviado com sucesso.")

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread


def send_selected_export_email_async(
    *,
    config: dict[str, Any],
    pdf_path: str | Path,
    json_path: str | Path | None = None,
    molde: str = "-",
    on_result: Callable[[bool, str], None] | None = None,
) -> threading.Thread:
    return _run_async(
        lambda: send_selected_export_email(
            config=config,
            pdf_path=pdf_path,
            json_path=json_path,
            molde=molde,
        ),
        on_result=on_result,
    )


def send_all_exports_email_async(
    *,
    config: dict[str, Any],
    on_result: Callable[[bool, str], None] | None = None,
) -> threading.Thread:
    return _run_async(
        lambda: send_all_exports_email(config=config),
        on_result=on_result,
    )


def should_send_automatically(config: dict[str, Any]) -> bool:
    automatic_config = config.get("automatic_send", {})
    return bool(config.get("enabled")) and bool(automatic_config.get("enabled"))


def send_automatic_exports_if_configured(
    *,
    pdf_path: str | Path | None = None,
    json_path: str | Path | None = None,
    molde: str = "-",
) -> tuple[bool, str]:
    try:
        config = load_email_config()
    except Exception as exc:
        return False, f"Email automático não configurado: {exc}"

    if not should_send_automatically(config):
        return False, "Email automático desativado."

    if not has_exported_pdf_json_pairs(config):
        return False, "Email automático ignorado: não existem pares PDF/JSON exportados."

    scope = str(config.get("automatic_send", {}).get("scope") or "last_export")

    try:
        if scope == "all_exports":
            send_all_exports_email_async(config=config)
            return True, "Envio automático de todos os exportados iniciado."

        if pdf_path is None:
            return False, "Email automático ignorado: PDF exportado não indicado."

        send_selected_export_email_async(
            config=config,
            pdf_path=pdf_path,
            json_path=json_path,
            molde=molde,
        )
        return True, "Envio automático do PDF exportado iniciado."
    except Exception as exc:
        return False, f"Email automático falhou: {exc}"


# ---------------------------------------------------------------------------
# Funções antigas mantidas como alternativa local: Outlook / ficheiro .eml
# ---------------------------------------------------------------------------

def open_email_with_attachments(
    subject: str,
    body: str,
    attachment_paths: Iterable[Path],
) -> tuple[bool, str]:
    paths = [Path(path) for path in attachment_paths]
    if not paths:
        return False, "Nao existem ficheiros para anexar."

    for path in paths:
        if not path.exists() or not path.is_file():
            return False, f"Ficheiro em falta: {path.name}"

    outlook_success, outlook_message = open_outlook_email(subject, body, paths)
    if outlook_success:
        return True, outlook_message

    try:
        draft_path = create_eml_draft(subject, body, paths)
        open_local_file(draft_path)
    except OSError as exc:
        return False, f"Nao foi possivel preparar o email: {exc}"

    return True, f"Email preparado: {draft_path.name}"


def open_outlook_email(subject: str, body: str, attachment_paths: list[Path]) -> tuple[bool, str]:
    try:
        import win32com.client  # type: ignore[import-not-found]
    except ImportError:
        return False, "Outlook COM indisponivel."

    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.Subject = subject
        mail.Body = body
        for path in attachment_paths:
            mail.Attachments.Add(str(path.resolve()))
        mail.Display()
    except Exception as exc:  # pragma: no cover - depends on local Outlook setup.
        return False, f"Outlook indisponivel: {exc}"

    return True, "Email aberto no Outlook com os anexos."


def create_eml_draft(subject: str, body: str, attachment_paths: list[Path]) -> Path:
    message = EmailMessage()
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid()
    message["X-Unsent"] = "1"
    message.set_content(body)

    for path in attachment_paths:
        content_type, encoding = mimetypes.guess_type(path.name)
        if content_type is None or encoding is not None:
            maintype, subtype = "application", "octet-stream"
        else:
            maintype, subtype = content_type.split("/", 1)
        message.add_attachment(
            path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )

    MAIL_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    draft_name = datetime.now().strftime("email_caudais_%Y%m%d_%H%M%S.eml")
    draft_path = MAIL_DRAFTS_DIR / draft_name
    counter = 1
    while draft_path.exists():
        draft_path = MAIL_DRAFTS_DIR / f"{Path(draft_name).stem}_{counter}.eml"
        counter += 1

    draft_path.write_bytes(message.as_bytes())
    return draft_path


def open_local_file(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
        return

    if not webbrowser.open(path.resolve().as_uri()):
        raise OSError("nao foi possivel abrir o rascunho de email")
