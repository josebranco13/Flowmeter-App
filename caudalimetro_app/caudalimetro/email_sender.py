from __future__ import annotations

import json
import mimetypes
import smtplib
import ssl
import threading
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Callable, Iterable

from .config import DATA_DIR, PDF_EXPORTS_DIR


EMAIL_CONFIG_PATH = DATA_DIR / "email_config.json"
EmailResultCallback = Callable[[bool, str], None]
EMAIL_SENT_FIELD = "email_enviado_em"


def load_email_config(config_path: str | Path = EMAIL_CONFIG_PATH) -> dict[str, Any]:
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Ficheiro de configuração não encontrado: {path}")

    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError("Configuração de email inválida.")

    return config


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():
        return [value.strip()]

    return []


def _format_template(template: str, context: dict[str, Any]) -> str:
    try:
        return template.format(**context)
    except KeyError:
        return template


def _export_directory(config: dict[str, Any] | None = None) -> Path:
    if not config:
        return PDF_EXPORTS_DIR

    export_dir = config.get("exports", {}).get("directory")

    if not export_dir:
        return PDF_EXPORTS_DIR

    path = Path(str(export_dir))

    if path.is_absolute():
        return path

    return DATA_DIR.parent / path


def export_manifest_was_emailed(json_path: Path) -> bool:
    try:
        with Path(json_path).open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return False

    return isinstance(data, dict) and bool(data.get(EMAIL_SENT_FIELD))


def mark_export_manifest_emailed(json_path: Path) -> bool:
    path = Path(json_path)
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return False

    if not isinstance(data, dict):
        return False

    from datetime import datetime

    data[EMAIL_SENT_FIELD] = datetime.now().isoformat(timespec="seconds")
    data["email_estado"] = "enviado"

    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except OSError:
        return False

    return True


def exported_pdf_json_pairs(
    export_dir: Path = PDF_EXPORTS_DIR,
) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []

    if not export_dir.exists():
        return pairs

    for pdf_path in sorted(export_dir.glob("*.pdf")):
        json_path = pdf_path.with_suffix(".json")

        if json_path.exists() and json_path.is_file():
            if export_manifest_was_emailed(json_path):
                continue
            pairs.append((pdf_path, json_path))

    return pairs


def has_exported_pdf_json_pairs(config: dict[str, Any] | None = None) -> bool:
    return bool(exported_pdf_json_pairs(_export_directory(config)))


def _smtp_send_message(config: dict[str, Any], message: EmailMessage) -> None:
    if not config.get("enabled", False):
        raise RuntimeError("O envio de email está desativado.")

    smtp_config = config["smtp"]
    account = config["account"]
    recipients = config["recipients"]

    password = str(account.get("password") or "").strip()

    if not password:
        raise RuntimeError("Password de email em falta no email_config.json.")

    to_recipients = _as_list(recipients.get("to"))
    cc_recipients = _as_list(recipients.get("cc"))
    bcc_recipients = _as_list(recipients.get("bcc"))

    all_recipients = to_recipients + cc_recipients + bcc_recipients

    if not all_recipients:
        raise RuntimeError("Não existem destinatários configurados.")

    sender_email = str(account["sender_email"])
    username = str(account.get("username") or sender_email)

    timeout = int(smtp_config.get("timeout_seconds", 20))
    security = str(smtp_config.get("security", "starttls")).lower()

    ssl_context = ssl.create_default_context()

    if security == "ssl":
        with smtplib.SMTP_SSL(
            str(smtp_config["host"]),
            int(smtp_config["port"]),
            timeout=timeout,
            context=ssl_context,
        ) as server:
            server.login(username, password)
            server.send_message(
                message,
                from_addr=sender_email,
                to_addrs=all_recipients,
            )
        return

    with smtplib.SMTP(
        str(smtp_config["host"]),
        int(smtp_config["port"]),
        timeout=timeout,
    ) as server:
        server.ehlo()

        if security == "starttls":
            server.starttls(context=ssl_context)
            server.ehlo()

        server.login(username, password)
        server.send_message(
            message,
            from_addr=sender_email,
            to_addrs=all_recipients,
        )


def send_email_with_attachments(
    *,
    config: dict[str, Any],
    subject: str,
    body: str,
    attachment_paths: Iterable[Path],
) -> tuple[bool, str]:
    paths = [Path(path) for path in attachment_paths]

    if not paths:
        return False, "Não existem ficheiros para enviar."

    for path in paths:
        if not path.exists() or not path.is_file():
            return False, f"Ficheiro em falta: {path.name}"

    try:
        account = config["account"]
        recipients = config["recipients"]

        to_recipients = _as_list(recipients.get("to"))
        cc_recipients = _as_list(recipients.get("cc"))

        sender_name = str(account.get("sender_name") or "").strip()
        sender_email = str(account["sender_email"])

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

        for path in paths:
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

        _smtp_send_message(config, message)

    except Exception as exc:
        return False, f"Não foi possível enviar o email: {exc}"

    return True, f"Email enviado com {len(paths)} anexo(s)."


def send_selected_export_email(
    *,
    config: dict[str, Any],
    pdf_path: Path,
    json_path: Path,
    mold: str | None = None,
    molde: str | None = None,
    file_name: str | None = None,
) -> tuple[bool, str]:
    pdf_path = Path(pdf_path)
    json_path = Path(json_path)

    if not pdf_path.exists():
        return False, f"Ficheiro em falta: {pdf_path.name}"

    if not json_path.exists():
        return False, f"Ficheiro em falta: {json_path.name}"

    message_config = config.get("messages", {}).get("single", {})
    selected_mold = str(mold if mold is not None else molde or "").strip() or "-"
    selected_file_name = str(file_name or pdf_path.name)

    context = {
        "molde": selected_mold,
        "mold": selected_mold,
        "ficheiro": selected_file_name,
        "pdf_nome": pdf_path.name,
        "json_nome": json_path.name,
        "total_ficheiros": 2,
    }

    subject = _format_template(
        str(message_config.get("subject") or "Registo de caudais - Molde {molde}"),
        context,
    )

    body = _format_template(
        str(
            message_config.get("body")
            or "Segue em anexo o PDF de registo de caudais e o respetivo JSON."
        ),
        context,
    )

    success, message = send_email_with_attachments(
        config=config,
        subject=subject,
        body=body,
        attachment_paths=[pdf_path, json_path],
    )
    if success:
        mark_export_manifest_emailed(json_path)
    return success, message


def send_all_exports_email(
    config: dict[str, Any],
    pairs: Iterable[tuple[Path, Path]] | None = None,
) -> tuple[bool, str]:
    pairs = list(pairs) if pairs is not None else exported_pdf_json_pairs(
        _export_directory(config)
    )

    if not pairs:
        return False, "Não existem pares PDF + JSON para enviar."

    attachments: list[Path] = []

    for pdf_path, json_path in pairs:
        attachments.append(pdf_path)
        attachments.append(json_path)

    message_config = config.get("messages", {}).get("all", {})

    context = {
        "total_pares": len(pairs),
        "total_pdfs": len(pairs),
        "total_ficheiros": len(attachments),
    }

    subject = _format_template(
        str(message_config.get("subject") or "Registos de caudais exportados"),
        context,
    )

    body = _format_template(
        str(
            message_config.get("body")
            or "Seguem em anexo todos os PDFs exportados e os respetivos JSON."
        ),
        context,
    )

    success, message = send_email_with_attachments(
        config=config,
        subject=subject,
        body=body,
        attachment_paths=attachments,
    )
    if success:
        for _pdf_path, json_path in pairs:
            mark_export_manifest_emailed(json_path)
    return success, message


def should_send_automatically(config: dict[str, Any]) -> bool:
    automatic_config = config.get("automatic_send", {})

    if not config.get("enabled", False):
        return False

    if not automatic_config.get("enabled", False):
        return False

    if automatic_config.get("require_pdf_and_json", True):
        return has_exported_pdf_json_pairs(config)

    return True


def _send_email_async(
    send_func: Callable[[], tuple[bool, str]],
    on_result: EmailResultCallback | None,
) -> threading.Thread:
    def run() -> None:
        try:
            success, message = send_func()
        except Exception as exc:
            success, message = False, str(exc)

        if on_result is not None:
            on_result(success, message)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread


def send_selected_export_email_async(
    *,
    config: dict[str, Any],
    pdf_path: Path,
    json_path: Path,
    mold: str | None = None,
    molde: str | None = None,
    file_name: str | None = None,
    on_result: EmailResultCallback | None = None,
) -> threading.Thread:
    return _send_email_async(
        lambda: send_selected_export_email(
            config=config,
            pdf_path=pdf_path,
            json_path=json_path,
            mold=mold,
            molde=molde,
            file_name=file_name,
        ),
        on_result,
    )


def send_all_exports_email_async(
    *,
    config: dict[str, Any],
    pairs: Iterable[tuple[Path, Path]] | None = None,
    on_result: EmailResultCallback | None = None,
) -> threading.Thread:
    return _send_email_async(lambda: send_all_exports_email(config, pairs), on_result)


def send_automatic_exports_if_configured(
    *,
    pdf_path: Path | None = None,
    json_path: Path | None = None,
    mold: str | None = None,
    molde: str | None = None,
    config_path: str | Path = EMAIL_CONFIG_PATH,
) -> tuple[bool, str]:
    try:
        config = load_email_config(config_path)
    except Exception as exc:
        return False, f"Configuracao de email invalida: {exc}"

    if not should_send_automatically(config):
        return False, "Envio automatico desativado."

    automatic_config = config.get("automatic_send", {})
    scope = str(automatic_config.get("scope") or "last_export").strip().casefold()

    if scope == "all":
        return send_all_exports_email(config)

    if pdf_path is None or json_path is None:
        return False, "Ficheiros de exportacao em falta."

    return send_selected_export_email(
        config=config,
        pdf_path=Path(pdf_path),
        json_path=Path(json_path),
        mold=mold,
        molde=molde,
        file_name=Path(pdf_path).name,
    )
