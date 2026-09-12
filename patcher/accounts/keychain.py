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


def delete_current_token_raw() -> bool:
    """
    Безопасно удаляет текущий токен из связки ключей без отправки сетевого запроса на отзыв (revoke).
    Используется мастером авторизации для подготовки входа в новый аккаунт.
    """
    if sys.platform == "darwin":
        try:
            res = subprocess.run(
                ["security", "delete-generic-password", "-s", SERVICE_NAME, "-a", ACCOUNT_NAME],
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0 or "could not be found" in res.stderr.lower()
        except Exception:
            return False
    elif sys.platform.startswith("linux"):
        try:
            res = subprocess.run(
                ["secret-tool", "clear", "service", SERVICE_NAME, "account", ACCOUNT_NAME],
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return False
    elif os.name == "nt":
        ps_script = f"""
        [void][Windows.Security.Credentials.PasswordVault,Windows.Security.Credentials,ContentType=WindowsRuntime]
        $vault = New-Object Windows.Security.Credentials.PasswordVault
        try {{
            $cred = $vault.Retrieve('{SERVICE_NAME}', '{ACCOUNT_NAME}')
            if ($cred) {{ $vault.Remove($cred) }}
            Write-Output "OK"
        }} catch {{}}
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


OAUTH_CLIENT_ID = "1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com"
OAUTH_CLIENT_SECRET = "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"


def _get_url_opener():
    """Создает URL opener с автоматической поддержкой локального системного прокси."""
    proxy_host = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    if not proxy_host:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.15)
        try:
            if s.connect_ex(("127.0.0.1", 1082)) == 0:
                proxy_host = "http://127.0.0.1:1082"
        except Exception:
            pass
        finally:
            s.close()

    if proxy_host:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy_host, "https": proxy_host})
        )
    return urllib.request.build_opener()


def refresh_google_oauth_token(refresh_token: str) -> dict:
    """
    Автоматически обновляет устаревший access_token через официальный эндпоинт Google OAuth,
    используя credentials Antigravity. Предотвращает разлогинивание аккаунтов.
    Если Google сообщает об ошибке invalid_grant (токен отозван/сброшен), возвращает флаг revoked=True.
    """
    if not refresh_token:
        return {}

    import urllib.parse
    import datetime

    data = urllib.parse.urlencode({
        "client_id": OAUTH_CLIENT_ID,
        "client_secret": OAUTH_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "antigravity/2.12.2",
        },
    )

    opener = _get_url_opener()
    try:
        with opener.open(req, timeout=7) as resp:
            if resp.status == 200:
                res = json.loads(resp.read().decode("utf-8"))
                expires_in = res.get("expires_in", 3600)
                expiry_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)
                res["expiry"] = expiry_dt.isoformat()
                return res
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
            if err_json.get("error") == "invalid_grant":
                return {
                    "error": "invalid_grant",
                    "error_description": err_json.get("error_description", "Токен был отозван или сброшен сервером Google"),
                    "revoked": True,
                }
        except Exception:
            pass
    except Exception:
        pass

    return {}


def decode_jwt_payload_offline(jwt_token: str) -> dict:
    """
    Безопасно декодирует полезную нагрузку JWT без внешних сетевых запросов.
    Используется для локального чтения email и имени из id_token Google OAuth.
    """
    if not jwt_token or "." not in jwt_token:
        return {}
    try:
        parts = jwt_token.strip().split(".")
        if len(parts) < 2:
            return {}
        payload_b64 = parts[1]
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)
        decoded = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        data = json.loads(decoded.decode("utf-8"))
        return {
            "email": data.get("email", ""),
            "name": data.get("name", ""),
            "picture": data.get("picture", ""),
            "sub": data.get("sub", ""),
        }
    except Exception:
        return {}


def fetch_google_account_info(access_token: str, id_token: str = "", allow_network: bool = True, timeout: int = 4) -> dict:
    """
    Возвращает реальную информацию об аккаунте (email, имя, аватар).
    1. Пробует декодировать id_token локально (офлайн).
    2. Если email не найден и allow_network=True, обращается к Google OAuth userinfo.
    """
    # 1. Приоритет: локальное декодирование id_token
    if id_token:
        offline_info = decode_jwt_payload_offline(id_token)
        if offline_info.get("email"):
            return offline_info

    # 2. Обращение к Google Userinfo с действующим access_token
    if not allow_network or not access_token:
        return {}

    url = "https://www.googleapis.com/oauth2/v3/userinfo"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "antigravity/2.12.2",
        },
    )

    opener = _get_url_opener()
    try:
        with opener.open(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "email": data.get("email", ""),
                    "name": data.get("name", ""),
                    "picture": data.get("picture", ""),
                    "sub": data.get("sub", ""),
                }
    except Exception:
        pass

    return {}


def format_seconds_to_ru_time(seconds: int) -> str:
    """Форматирует секунды в читаемое время на русском (например: '1 ч. 42 мин.' или '5 дн. 18 ч.')."""
    if seconds <= 0:
        return "0 сек."
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if days > 0:
        return f"{days} дн. {hours} ч."
    if hours > 0:
        return f"{hours} ч. {minutes} мин."
    if minutes > 0:
        return f"{minutes} мин. {secs} сек."
    return f"{secs} сек."


def fetch_local_language_server_quota() -> dict:
    """
    Запрашивает актуальный статус квот напрямую у запущенного локального процесса language_server.
    Работает мгновенно (10 мс) и на 100% офлайн без обращения во внешнюю сеть.
    """
    try:
        import ssl
        import re

        out = subprocess.run(["ps", "aux"], capture_output=True, text=True, check=False).stdout
        pid, csrf = None, None
        for line in out.splitlines():
            if "language_server" in line and "--csrf_token" in line:
                m_csrf = re.search(r"--csrf_token\s+([a-zA-Z0-9-]+)", line)
                if m_csrf:
                    csrf = m_csrf.group(1)
                    parts = line.strip().split()
                    pid = parts[1]
                    break

        if not pid or not csrf:
            return {}

        lsof = subprocess.run(
            ["lsof", "-a", "-p", str(pid), "-iTCP", "-sTCP:LISTEN", "-nP"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        ports = [int(p) for p in re.findall(r":(\d+)\s+\(LISTEN\)", lsof)]

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=ctx),
        )

        for port in ports:
            try:
                req = urllib.request.Request(
                    f"https://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary",
                    data=b"{}",
                    headers={"x-codeium-csrf-token": csrf, "Content-Type": "application/json"},
                    method="POST",
                )
                with opener.open(req, timeout=1.5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        resp_obj = data.get("response", {})
                        if resp_obj and "groups" in resp_obj:
                            return parse_quota_response(resp_obj)
            except Exception:
                continue
    except Exception:
        pass

    return {}


def fetch_user_quota_summary(access_token: str, force_remote: bool = False) -> dict:
    """
    Запрашивает актуальный баланс квот и лимитов (5-часовой и недельный).
    1. Приоритет (для активного слота): опрос локального language_server (10 мс, 100% офлайн).
    2. Fallback или force_remote (для неактивных слотов): официальный внешний эндпоинт Cloud Code / Antigravity.
    """
    # 1. Приоритет: локальный language_server (только если не запрошен прямой опрос конкретного токена)
    if not force_remote:
        local_quota = fetch_local_language_server_quota()
        if local_quota and (local_quota.get("gemini_5h") or local_quota.get("gemini_weekly")):
            return local_quota

    if not access_token:
        return {}

    url = "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary"
    req = urllib.request.Request(
        url,
        data=b"{}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "antigravity/2.12.2",
        },
        method="POST",
    )

    opener = _get_url_opener()
    try:
        with opener.open(req, timeout=4) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return parse_quota_response(data)
    except Exception:
        pass

    return {}


def parse_quota_response(raw_data: dict) -> dict:
    """
    Парсит ответ retrieveUserQuotaSummary в чистую структуру для UI.
    """
    import datetime

    result = {
        "gemini_5h": None,
        "gemini_weekly": None,
        "claude_5h": None,
        "claude_weekly": None,
        "raw_groups": raw_data.get("groups", []),
    }

    now_utc = datetime.datetime.now(datetime.timezone.utc)

    for group in raw_data.get("groups", []):
        group_name = group.get("displayName", "").lower()
        is_gemini = "gemini" in group_name
        is_claude = any(x in group_name for x in ["claude", "gpt", "third_party", "3p"])

        for bucket in group.get("buckets", []):
            window = bucket.get("window", "").lower()
            remaining_frac = bucket.get("remainingFraction", 1.0)
            remaining_pct = round(remaining_frac * 100, 1)
            reset_time_str = bucket.get("resetTime", "")

            # Расчет оставшихся секунд до сброса
            reset_in_seconds = 0
            if reset_time_str:
                try:
                    # ISO 8601 parsing: 2026-09-12T14:36:24Z
                    clean_time = reset_time_str.replace("Z", "+00:00")
                    reset_dt = datetime.datetime.fromisoformat(clean_time)
                    diff = (reset_dt - now_utc).total_seconds()
                    reset_in_seconds = max(0, int(diff))
                except Exception:
                    pass

            bucket_info = {
                "display_name": bucket.get("displayName", ""),
                "window": window,
                "remaining_fraction": remaining_frac,
                "remaining_pct": remaining_pct,
                "reset_time": reset_time_str,
                "reset_in_seconds": reset_in_seconds,
                "formatted_reset": format_seconds_to_ru_time(reset_in_seconds),
                "description": bucket.get("description", ""),
            }

            if is_gemini:
                if "5h" in window or "five" in bucket.get("displayName", "").lower():
                    result["gemini_5h"] = bucket_info
                elif "weekly" in window or "week" in bucket.get("displayName", "").lower():
                    result["gemini_weekly"] = bucket_info
            elif is_claude:
                if "5h" in window or "five" in bucket.get("displayName", "").lower():
                    result["claude_5h"] = bucket_info
                elif "weekly" in window or "week" in bucket.get("displayName", "").lower():
                    result["claude_weekly"] = bucket_info

    return result

