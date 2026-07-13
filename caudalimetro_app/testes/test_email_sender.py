from __future__ import annotations

import base64
import json
import sys
import unittest
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from caudalimetro import email_sender, gmail_sender  # noqa: E402


def email_config() -> dict[str, object]:
    return {
        "enabled": True,
        "account": {
            "sender_name": "Sistema de Medição de Caudais",
            "sender_email": "sender@example.com",
        },
        "recipients": {
            "to": ["to@example.com"],
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"],
        },
        "messages": {
            "single": {
                "subject": "Registo de caudais - Molde {molde}",
                "body": "Relatório do molde {molde}: {ficheiro}",
            },
            "all": {
                "subject": "Registo de caudais - {identificacao_moldes}",
                "body": "Relatórios dos moldes {moldes}; anexos: {total_ficheiros}",
            },
        },
    }


def create_export_pair(directory: Path, mold_id: str) -> tuple[Path, Path]:
    pdf_path = directory / f"Registo_Caudais_{mold_id}.pdf"
    json_path = pdf_path.with_suffix(".json")
    pdf_path.write_bytes(b"%PDF-1.4\n% test\n")
    json_path.write_text(
        json.dumps(
            {
                "molde": mold_id,
                "ficheiro": pdf_path.name,
                "medicoes": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return pdf_path, json_path


class EmailSenderTests(unittest.TestCase):
    def test_selected_export_uses_gmail_with_pdf_and_json(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            pdf_path, json_path = create_export_pair(
                Path(temporary_directory),
                "AHA1",
            )
            sent_messages: list[EmailMessage] = []

            with patch.object(
                email_sender,
                "send_gmail_message",
                side_effect=lambda message: sent_messages.append(message) or "gmail-id",
            ):
                success, result = email_sender.send_selected_export_email(
                    config=email_config(),
                    pdf_path=pdf_path,
                    json_path=json_path,
                    molde="AHA1",
                )

            self.assertTrue(success, result)
            self.assertEqual(len(sent_messages), 1)
            message = sent_messages[0]
            self.assertEqual(message["Subject"], "Registo de caudais - Molde AHA1")
            self.assertEqual(message["To"], "to@example.com")
            self.assertEqual(message["Cc"], "cc@example.com")
            self.assertEqual(message["Bcc"], "bcc@example.com")
            self.assertEqual(
                [part.get_filename() for part in message.iter_attachments()],
                [pdf_path.name, json_path.name],
            )
            self.assertEqual(
                [part.get_content_type() for part in message.iter_attachments()],
                ["application/pdf", "application/json"],
            )

            marked_manifest = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(marked_manifest["email_estado"], "enviado")
            self.assertTrue(marked_manifest[email_sender.EMAIL_SENT_FIELD])

    def test_all_exports_lists_every_mold_and_attaches_every_pair(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            pair_2 = create_export_pair(directory, "AHA2")
            pair_1 = create_export_pair(directory, "AHA1")
            sent_messages: list[EmailMessage] = []

            with patch.object(
                email_sender,
                "send_gmail_message",
                side_effect=lambda message: sent_messages.append(message) or "gmail-id",
            ):
                success, result = email_sender.send_all_exports_email(
                    email_config(),
                    [pair_2, pair_1],
                )

            self.assertTrue(success, result)
            self.assertEqual(len(sent_messages), 1)
            message = sent_messages[0]
            self.assertEqual(
                message["Subject"],
                "Registo de caudais - Moldes AHA1, AHA2",
            )
            self.assertEqual(
                [part.get_filename() for part in message.iter_attachments()],
                [
                    pair_2[0].name,
                    pair_2[1].name,
                    pair_1[0].name,
                    pair_1[1].name,
                ],
            )

            for _pdf_path, json_path in (pair_2, pair_1):
                manifest = json.loads(json_path.read_text(encoding="utf-8"))
                self.assertTrue(manifest[email_sender.EMAIL_SENT_FIELD])

    def test_failed_gmail_send_does_not_mark_manifest(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            pdf_path, json_path = create_export_pair(
                Path(temporary_directory),
                "AHA3",
            )

            with patch.object(
                email_sender,
                "send_gmail_message",
                side_effect=RuntimeError("falha simulada"),
            ):
                success, result = email_sender.send_selected_export_email(
                    config=email_config(),
                    pdf_path=pdf_path,
                    json_path=json_path,
                    molde="AHA3",
                )

            self.assertFalse(success)
            self.assertIn("falha simulada", result)
            manifest = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertNotIn(email_sender.EMAIL_SENT_FIELD, manifest)

    def test_all_exports_rejects_manifest_without_mold_id(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            pdf_path, json_path = create_export_pair(
                Path(temporary_directory),
                "AHA4",
            )
            json_path.write_text("{}", encoding="utf-8")

            with patch.object(email_sender, "send_gmail_message") as send_message:
                success, result = email_sender.send_all_exports_email(
                    email_config(),
                    [(pdf_path, json_path)],
                )

            self.assertFalse(success)
            self.assertIn("ID do molde em falta", result)
            send_message.assert_not_called()

    def test_custom_subject_does_not_confuse_prefix_mold_ids(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            pdf_path, json_path = create_export_pair(
                Path(temporary_directory),
                "AHA1",
            )
            config = email_config()
            config["messages"]["single"]["subject"] = "Relatório do molde AHA10"
            sent_messages: list[EmailMessage] = []

            with patch.object(
                email_sender,
                "send_gmail_message",
                side_effect=lambda message: sent_messages.append(message) or "gmail-id",
            ):
                success, result = email_sender.send_selected_export_email(
                    config=config,
                    pdf_path=pdf_path,
                    json_path=json_path,
                    molde="AHA1",
                )

            self.assertTrue(success, result)
            self.assertEqual(
                sent_messages[0]["Subject"],
                "Relatório do molde AHA10 - Molde AHA1",
            )

    def test_success_reports_warning_when_manifest_cannot_be_marked(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            pdf_path, json_path = create_export_pair(
                Path(temporary_directory),
                "AHA6",
            )

            with (
                patch.object(email_sender, "send_gmail_message", return_value="gmail-id"),
                patch.object(
                    email_sender,
                    "mark_export_manifest_emailed",
                    return_value=False,
                ),
            ):
                success, result = email_sender.send_selected_export_email(
                    config=email_config(),
                    pdf_path=pdf_path,
                    json_path=json_path,
                    molde="AHA6",
                )

            self.assertTrue(success)
            self.assertIn("email foi enviado", result)
            self.assertIn("não foi possível atualizar", result)

    def test_export_pair_discovery_ignores_unrelated_files(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            expected_pair = create_export_pair(directory, "AHA7")
            unrelated_pdf = directory / "outro_relatorio.pdf"
            unrelated_json = unrelated_pdf.with_suffix(".json")
            unrelated_pdf.write_bytes(b"%PDF-1.4\n")
            unrelated_json.write_text(
                json.dumps(
                    {"molde": "OUTRO", "ficheiro": unrelated_pdf.name},
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                email_sender.exported_pdf_json_pairs(directory),
                [expected_pair],
            )


class GmailSenderTests(unittest.TestCase):
    def test_gmail_transport_sends_base64url_encoded_mime_message(self) -> None:
        message = EmailMessage()
        message["From"] = "sender@example.com"
        message["To"] = "to@example.com"
        message["Subject"] = "Registo de caudais - Molde AHA5"
        message.set_content("Teste")
        message.add_attachment(
            b"%PDF-1.4\n",
            maintype="application",
            subtype="pdf",
            filename="Registo_Caudais_AHA5.pdf",
        )

        service = MagicMock()
        send_call = service.users.return_value.messages.return_value.send
        send_call.return_value.execute.return_value = {"id": "gmail-message-id"}

        with (
            patch.object(gmail_sender, "obter_credenciais", return_value=object()),
            patch.object(gmail_sender, "_build_gmail_service", return_value=service),
        ):
            message_id = gmail_sender.send_gmail_message(message)

        self.assertEqual(message_id, "gmail-message-id")
        send_call.assert_called_once()
        call_arguments = send_call.call_args.kwargs
        self.assertEqual(call_arguments["userId"], "me")

        decoded_message = base64.urlsafe_b64decode(call_arguments["body"]["raw"])
        parsed_message = BytesParser(policy=policy.default).parsebytes(decoded_message)
        self.assertEqual(
            parsed_message["Subject"],
            "Registo de caudais - Molde AHA5",
        )
        self.assertEqual(
            [part.get_filename() for part in parsed_message.iter_attachments()],
            ["Registo_Caudais_AHA5.pdf"],
        )


if __name__ == "__main__":
    unittest.main()
