from __future__ import annotations

import base64
import hashlib
import hmac
import os
import sqlite3

from .config import DATA_DIR


DATABASE_PATH = DATA_DIR / "users.db"

HASH_ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
SALT_SIZE = 16


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:
    """Cria a base de dados e a tabela users."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                password_hash TEXT NOT NULL
            )
            """
        )


def normalize_username(username: str) -> str:
    return username.strip().upper()


def hash_password(password: str) -> str:
    """
    Gera uma hash PBKDF2-HMAC-SHA256.

    O salt, o número de iterações e a hash ficam todos guardados
    na coluna password_hash.
    """

    if not password:
        raise ValueError("A password não pode estar vazia.")

    salt = os.urandom(SALT_SIZE)

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
    )

    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii")
    encoded_hash = base64.urlsafe_b64encode(derived_key).decode("ascii")

    return (
        f"{HASH_ALGORITHM}$"
        f"{ITERATIONS}$"
        f"{encoded_salt}$"
        f"{encoded_hash}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifica uma password sem recuperar a password original."""

    try:
        algorithm, iterations_text, encoded_salt, encoded_hash = (
            stored_hash.split("$", 3)
        )

        if algorithm != HASH_ALGORITHM:
            return False

        iterations = int(iterations_text)

        salt = base64.urlsafe_b64decode(
            encoded_salt.encode("ascii")
        )

        expected_hash = base64.urlsafe_b64decode(
            encoded_hash.encode("ascii")
        )

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )

        return hmac.compare_digest(
            calculated_hash,
            expected_hash,
        )

    except (ValueError, TypeError):
        return False


def create_user(username: str, password: str) -> tuple[bool, str]:
    username = normalize_username(username)
    password = password.strip()

    if not username:
        return False, "Indique o nome do utilizador."

    if not password:
        return False, "Indique a password ou PIN."

    password_hash = hash_password(password)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    username,
                    password_hash
                )
                VALUES (?, ?)
                """,
                (username, password_hash),
            )

        return True, f"Utilizador {username} criado."

    except sqlite3.IntegrityError:
        return False, f"O utilizador {username} já existe."


def change_user_password(
    username: str,
    new_password: str,
) -> tuple[bool, str]:
    username = normalize_username(username)
    new_password = new_password.strip()

    if not username:
        return False, "Indique o nome do utilizador."

    if not new_password:
        return False, "Indique a nova password ou PIN."

    password_hash = hash_password(new_password)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE username = ?
            """,
            (password_hash, username),
        )

    if cursor.rowcount == 0:
        return False, f"O utilizador {username} não existe."

    return True, f"Password de {username} alterada."


def authenticate_user(username: str, password: str) -> bool:
    """Valida o username e o PIN introduzidos no login."""

    username = normalize_username(username)

    if not username or not password:
        return False

    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT password_hash
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    if user is None:
        return False

    return verify_password(
        password,
        user["password_hash"],
    )


def get_usernames() -> list[str]:
    """Obtém apenas os usernames para a lista de operadores."""

    with get_connection() as connection:
        users = connection.execute(
            """
            SELECT username
            FROM users
            ORDER BY
                CASE
                    WHEN username = 'ADMIN' THEN 0
                    ELSE 1
                END,
                username COLLATE NOCASE
            """
        ).fetchall()

    return [user["username"] for user in users]


def delete_user(username: str) -> tuple[bool, str]:
    username = normalize_username(username)

    if username == "ADMIN":
        return False, "O utilizador ADMIN não pode ser removido."

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM users
            WHERE username = ?
            """,
            (username,),
        )

    if cursor.rowcount == 0:
        return False, f"O utilizador {username} não existe."

    return True, f"Utilizador {username} removido."