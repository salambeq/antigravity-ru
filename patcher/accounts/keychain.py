#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Кроссплатформенный адаптер для взаимодействия со связкой ключей операционной системы.
Используется Antigravity и language_server для хранения токенов авторизации Google OAuth.
"""

import os
import sys
import json
import base64
import subprocess
import urllib.request
import urllib.error

SERVICE_NAME = "gemini"
ACCOUNT_NAME = "antigravity"
KEYRING_PREFIX = "go-keyring-base64:"


def decode_token_payload(raw_value: str) -> dict:
    """Декодирует строку формата go-keyring-base64 в словарь Python."""
    if not raw_value:
        return {}
    raw_value = raw_value.strip()
    if raw_value.startswith(KEYRING_PREFIX):
        raw_b64 = raw_value[len(KEYRING_PREFIX):]
    else:
        raw_b64 = raw_value

    try:
        decoded_bytes = base64.b64decode(raw_b64)
        return json.loads(decoded_bytes.decode("utf-8"))
    except Exception as e:
        return {"error": f"Failed to decode token payload: {e}", "raw": raw_value}


def encode_token_payload(data: dict) -> str:
    """Кодирует словарь данных в формат go-keyring-base64."""
    json_str = json.dumps(data, separators=(",", ":"))
    b64_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    return f"{KEYRING_PREFIX}{b64_str}"


def read_current_token_raw() -> str:
    """
    Считывает текущую сырую строку токена из системного хранилища ключей.
    Возвращает пустую строку, если ключ не найден.
    """
    if sys.platform == "darwin":
        try:
            res = subprocess.run(
                ["security", "find-generic-password", "-s", SERVICE_NAME, "-a", ACCOUNT_NAME, "-w"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        # Попытка через secret-tool
        try:
            res = subprocess.run(
                ["secret-tool", "lookup", "service", SERVICE_NAME, "account", ACCOUNT_NAME],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
    elif os.name == "nt":
        # Попытка через PowerShell Credential Manager
        ps_script = f"""
        [void][Windows.Security.Credentials.PasswordVault,Windows.Security.Credentials,ContentType=WindowsRuntime]
        $vault = New-Object Windows.Security.Credentials.PasswordVault
        try {{
            $cred = $vault.Retrieve('{SERVICE_NAME}', '{ACCOUNT_NAME}')
            $cred.FillPassword()
            Write-Output $cred.Password
        }} catch {{}}
        """
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    return ""


def write_token_raw(raw_value: str) -> bool:
    """
    Записывает сырую строку токена в системное хранилище ключей.
    """
    if not raw_value:
        return False

    raw_value = raw_value.strip()

    if sys.platform == "darwin":
        try:
            res = subprocess.run(
                ["security", "add-generic-password", "-U", "-s", SERVICE_NAME, "-a", ACCOUNT_NAME, "-w", raw_value],
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return False

    elif sys.platform.startswith("linux"):
        try:
            p = subprocess.Popen(
                ["secret-tool", "store", f"--label=Antigravity Token", "service", SERVICE_NAME, "account", ACCOUNT_NAME],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input=raw_value)
            return p.returncode == 0
        except Exception:
            return False

    elif os.name == "nt":
        ps_script = f"""
        [void][Windows.Security.Credentials.PasswordVault,Windows.Security.Credentials,ContentType=WindowsRuntime]
        $vault = New-Object Windows.Security.Credentials.PasswordVault
        $cred = New-Object Windows.Security.Credentials.PasswordCredential('{SERVICE_NAME}', '{ACCOUNT_NAME}', '{raw_value}')
        $vault.Add($cred)
        """
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return False

    return False


def fetch_google_account_info(access_token: str, timeout: int = 3) -> dict:
    """
    Запрашивает базовую информацию об аккаунте (email, name) через Google OAuth userinfo API.
    """
    if not access_token:
        return {}

    url = "https://www.googleapis.com/oauth2/v3/userinfo"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "email": data.get("email", ""),
                    "name": data.get("name", ""),
                    "picture": data.get("picture", ""),
                }
    except Exception:
        pass

    return {}
