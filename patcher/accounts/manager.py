#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер профилей аккаунтов Antigravity.
Обеспечивает сохранение, переключение и ротацию слотов аккаунтов Google.
"""

from __future__ import annotations

import os
import sys
import time
import json
import shutil
import subprocess
import datetime

from patcher.accounts.keychain import (
    read_current_token_raw,
    write_token_raw,
    decode_token_payload,
    encode_token_payload,
    fetch_google_account_info,
    refresh_google_oauth_token,
    fetch_user_quota_summary,
)
from patcher.utils.console import info, ok, warn, err, step

DEFAULT_ACCOUNTS_DIR = os.path.expanduser("~/.gemini/accounts")


class AccountManager:
    def __init__(self, accounts_dir: str = DEFAULT_ACCOUNTS_DIR):
        self.accounts_dir = accounts_dir
        self.slots_dir = os.path.join(self.accounts_dir, "slots")
        self.meta_path = os.path.join(self.accounts_dir, "metadata.json")
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Создает необходимые директории с безопасными правами (0700)."""
        if not os.path.exists(self.slots_dir):
            os.makedirs(self.slots_dir, mode=0o700, exist_ok=True)
        try:
            os.chmod(self.accounts_dir, 0o700)
            os.chmod(self.slots_dir, 0o700)
        except OSError:
            pass

    def _load_metadata(self) -> dict:
        if os.path.isfile(self.meta_path):
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"active_slot": None, "slots": {}}

    def _save_metadata(self, meta: dict):
        self._ensure_dirs()
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(self.meta_path, 0o600)
        except OSError:
            pass

    def get_slot_path(self, slot_num: int) -> str:
        return os.path.join(self.slots_dir, f"slot_{slot_num}.json")

    def sync_keychain_to_active_slot(self):
        """
        Синхронизирует текущий токен из Keychain в файл активного слота.
        Предотвращает потерю токенов, когда language_server обновляет их в фоне.
        """
        raw = read_current_token_raw()
        if not raw:
            return

        meta = self._load_metadata()
        active_slot = meta.get("active_slot")
        if not active_slot:
            return

        slot_path = self.get_slot_path(active_slot)
        if not os.path.isfile(slot_path):
            return

        try:
            with open(slot_path, "r", encoding="utf-8") as f:
                slot_data = json.load(f)

            if slot_data.get("raw_payload") != raw:
                slot_data["raw_payload"] = raw
                slot_data["saved_at"] = int(time.time())

                payload = decode_token_payload(raw)
                tok = payload.get("token", {}) if isinstance(payload, dict) else {}
                access_token = tok.get("access_token", "")
                if access_token and (not slot_data.get("email") or slot_data.get("email", "").startswith("account_")):
                    uinfo = fetch_google_account_info(access_token)
                    if uinfo.get("email"):
                        slot_data["email"] = uinfo["email"]
                        slot_data["name"] = uinfo.get("name", "")
                        meta["slots"][str(active_slot)] = {
                            "email": slot_data["email"],
                            "name": slot_data["name"],
                            "saved_at": slot_data["saved_at"],
                        }
                        self._save_metadata(meta)

                with open(slot_path, "w", encoding="utf-8") as f:
                    json.dump(slot_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def ensure_slot_token_fresh(self, slot_num: int) -> bool:
        """
        Проверяет срок действия токена в слоте. Если токен истёк или истекает в ближайшие 5 минут,
        автоматически обновляет его через refresh_google_oauth_token и сохраняет.
        Гарантирует, что аккаунт никогда не разлогинится («не слетит»).
        """
        slot_path = self.get_slot_path(slot_num)
        if not os.path.isfile(slot_path):
            return False

        try:
            with open(slot_path, "r", encoding="utf-8") as f:
                slot_data = json.load(f)

            raw = slot_data.get("raw_payload", "")
            if not raw:
                return False

            payload = decode_token_payload(raw)
            if not isinstance(payload, dict):
                return False

            tok = payload.get("token", {})
            access_token = tok.get("access_token", "")
            refresh_token = tok.get("refresh_token", "")
            expiry_str = tok.get("expiry", "")

            # Проверка необходимости обновления токена
            needs_refresh = False
            if not access_token:
                needs_refresh = True
            elif expiry_str:
                try:
                    clean_exp = expiry_str.replace("Z", "+00:00")
                    exp_dt = datetime.datetime.fromisoformat(clean_exp)
                    now_dt = datetime.datetime.now(datetime.timezone.utc)
                    if (exp_dt - now_dt).total_seconds() < 300:
                        needs_refresh = True
                except Exception:
                    needs_refresh = True
            else:
                needs_refresh = True

            updated = False
            if needs_refresh and refresh_token:
                refreshed = refresh_google_oauth_token(refresh_token)
                if refreshed.get("access_token"):
                    tok["access_token"] = refreshed["access_token"]
                    if refreshed.get("expiry"):
                        tok["expiry"] = refreshed["expiry"]
                    if refreshed.get("refresh_token"):
                        tok["refresh_token"] = refreshed["refresh_token"]
                    payload["token"] = tok
                    raw = encode_token_payload(payload)
                    slot_data["raw_payload"] = raw
                    slot_data["saved_at"] = int(time.time())
                    updated = True

            # Извлечение реального email/имени если они не заполнены
            cur_acc_token = tok.get("access_token")
            if cur_acc_token and (not slot_data.get("email") or slot_data.get("email", "").startswith("account_")):
                uinfo = fetch_google_account_info(cur_acc_token)
                if uinfo.get("email"):
                    slot_data["email"] = uinfo["email"]
                    slot_data["name"] = uinfo.get("name", "")
                    updated = True

            if updated:
                with open(slot_path, "w", encoding="utf-8") as f:
                    json.dump(slot_data, f, indent=2, ensure_ascii=False)

                meta = self._load_metadata()
                meta["slots"][str(slot_num)] = {
                    "email": slot_data["email"],
                    "name": slot_data.get("name", ""),
                    "saved_at": slot_data["saved_at"],
                }
                self._save_metadata(meta)

                # Если это текущий активный слот — обновляем и Keychain
                if meta.get("active_slot") == slot_num:
                    write_token_raw(raw)

            return True
        except Exception:
            return False

    def get_current_account_info(self) -> dict:
        """
        Возвращает данные текущего авторизованного в системе аккаунта.
        Автоматически обновляет истекающий токен и синхронизирует с активным слотом.
        """
        raw = read_current_token_raw()
        if not raw:
            return {"authenticated": False, "email": None, "error": "Токен не найден в связке ключей"}

        payload = decode_token_payload(raw)
        tok = payload.get("token", {}) if isinstance(payload, dict) else {}
        access_token = tok.get("access_token", "")
        refresh_token = tok.get("refresh_token", "")
        id_token = tok.get("id_token", "") or (payload.get("id_token", "") if isinstance(payload, dict) else "")
        expiry_str = tok.get("expiry", "")

        # Автоматическое продление текущего токена при необходимости
        needs_refresh = False
        if expiry_str:
            try:
                clean_exp = expiry_str.replace("Z", "+00:00")
                exp_dt = datetime.datetime.fromisoformat(clean_exp)
                now_dt = datetime.datetime.now(datetime.timezone.utc)
                if (exp_dt - now_dt).total_seconds() < 180:
                    needs_refresh = True
            except Exception:
                pass

        if needs_refresh and refresh_token:
            refreshed = refresh_google_oauth_token(refresh_token)
            if refreshed.get("access_token"):
                tok["access_token"] = refreshed["access_token"]
                access_token = refreshed["access_token"]
                if refreshed.get("expiry"):
                    tok["expiry"] = refreshed["expiry"]
                payload["token"] = tok
                raw = encode_token_payload(payload)
                write_token_raw(raw)

        account_info = {
            "authenticated": bool(access_token or refresh_token),
            "has_refresh_token": bool(refresh_token),
            "expiry": tok.get("expiry"),
            "email": None,
            "name": None,
            "picture": None,
            "raw": raw,
        }

        # Получение реального email и имени
        google_info = fetch_google_account_info(access_token, id_token=id_token, allow_network=True)
        if google_info.get("email"):
            account_info["email"] = google_info.get("email")
            account_info["name"] = google_info.get("name")
            account_info["picture"] = google_info.get("picture")

        # Синхронизация с активным слотом
        self.sync_keychain_to_active_slot()

        return account_info

    def save_current_account(self, slot_num: int, custom_label: str = "") -> tuple[bool, str]:
        """
        Сохраняет текущий активный в Antigravity аккаунт в указанный слот (1..N).
        """
        if slot_num < 1:
            return False, "Номер слота должен быть положительным числом (например, 1, 2, 3, 4)."

        cur = self.get_current_account_info()
        if not cur.get("authenticated") or not cur.get("raw"):
            return False, "В системе не обнаружен авторизованный аккаунт Antigravity. Сначала войдите в Google-аккаунт в приложении."

        slot_path = self.get_slot_path(slot_num)
        slot_data = {
            "slot": slot_num,
            "email": cur.get("email") or custom_label or f"account_{slot_num}@google",
            "name": cur.get("name") or "",
            "picture": cur.get("picture") or "",
            "saved_at": int(time.time()),
            "raw_payload": cur["raw"],
        }

        try:
            with open(slot_path, "w", encoding="utf-8") as f:
                json.dump(slot_data, f, indent=2, ensure_ascii=False)
            try:
                os.chmod(slot_path, 0o600)
            except OSError:
                pass

            meta = self._load_metadata()
            meta["slots"][str(slot_num)] = {
                "email": slot_data["email"],
                "name": slot_data["name"],
                "saved_at": slot_data["saved_at"],
            }
            meta["active_slot"] = slot_num
            self._save_metadata(meta)

            return True, f"Аккаунт {slot_data['email']} успешно сохранён в Слот #{slot_num}!"
        except Exception as e:
            return False, f"Ошибка при сохранении слота: {e}"

    def list_slots(self, auto_heal: bool = True) -> dict:
        """
        Возвращает список всех сохранённых слотов с их статусом.
        При auto_heal=True автоматически восстанавливает и продлевает устаревшие токены.
        """
        meta = self._load_metadata()
        slots = {}

        if os.path.exists(self.slots_dir):
            for fname in sorted(os.listdir(self.slots_dir)):
                if fname.startswith("slot_") and fname.endswith(".json"):
                    try:
                        num_part = fname[len("slot_") : -len(".json")]
                        slot_num = int(num_part)
                        fpath = os.path.join(self.slots_dir, fname)

                        if auto_heal:
                            self.ensure_slot_token_fresh(slot_num)

                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        slots[slot_num] = {
                            "email": data.get("email", f"Слот #{slot_num}"),
                            "name": data.get("name", ""),
                            "picture": data.get("picture", ""),
                            "saved_at": data.get("saved_at", 0),
                            "is_active": (slot_num == meta.get("active_slot")),
                        }
                    except Exception:
                        pass

        return slots

    def switch_to_slot(self, slot_num: int, restart_ls: bool = True) -> tuple[bool, str]:
        """
        Переключает текущий аккаунт Antigravity на указанный слот.
        1. Сохраняет текущее состояние Keychain в старый активный слот.
        2. Проверяет и обновляет токен нового слота через Google OAuth.
        3. Записывает свежий токен в Keychain.
        4. Мягко перезапускает language_server.
        """
        slot_path = self.get_slot_path(slot_num)
        if not os.path.isfile(slot_path):
            return False, f"Слот #{slot_num} не найден. Сначала сохраните в него аккаунт."

        # 1. Синхронизация текущего Keychain перед переключением
        self.sync_keychain_to_active_slot()

        # 2. Гарантия свежести целевого токена
        self.ensure_slot_token_fresh(slot_num)

        try:
            with open(slot_path, "r", encoding="utf-8") as f:
                slot_data = json.load(f)
            raw = slot_data.get("raw_payload", "")
            if not raw:
                return False, f"В слоте #{slot_num} повреждены данные токена."

            # 3. Записываем в системную связку ключей
            if not write_token_raw(raw):
                return False, "Не удалось записать токен в системное хранилище (Keychain)."

            # 4. Обновляем метаданные активного слота
            meta = self._load_metadata()
            meta["active_slot"] = slot_num
            self._save_metadata(meta)

            email_str = slot_data.get("email", f"Слот #{slot_num}")

            # 5. Перезапускаем language_server при необходимости
            if restart_ls:
                self.restart_language_server()

            return True, f"Успешно переключено на {email_str} (Слот #{slot_num})!"
        except Exception as e:
            return False, f"Ошибка переключения слота: {e}"

    def get_slot_quota_summary(self, slot_num: int = None) -> dict:
        """
        Возвращает баланс квот и лимитов (5-часовых и недельных) для указанного слота
        или для текущего активного аккаунта.
        """
        access_token = ""
        if slot_num is not None:
            self.ensure_slot_token_fresh(slot_num)
            slot_path = self.get_slot_path(slot_num)
            if os.path.isfile(slot_path):
                try:
                    with open(slot_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    payload = decode_token_payload(data.get("raw_payload", ""))
                    access_token = payload.get("token", {}).get("access_token", "")
                except Exception:
                    pass
        else:
            cur = self.get_current_account_info()
            raw = cur.get("raw", "")
            if raw:
                payload = decode_token_payload(raw)
                access_token = payload.get("token", {}).get("access_token", "")

        if not access_token:
            return {}

        return fetch_user_quota_summary(access_token)

    def delete_slot(self, slot_num: int) -> tuple[bool, str]:
        """Удаляет сохраненный слот."""
        slot_path = self.get_slot_path(slot_num)
        if os.path.isfile(slot_path):
            try:
                os.remove(slot_path)
                meta = self._load_metadata()
                if str(slot_num) in meta.get("slots", {}):
                    del meta["slots"][str(slot_num)]
                if meta.get("active_slot") == slot_num:
                    meta["active_slot"] = None
                self._save_metadata(meta)
                return True, f"Слот #{slot_num} удалён."
            except Exception as e:
                return False, f"Ошибка при удалении: {e}"
        return False, f"Слот #{slot_num} не существует."

    def get_next_slot_number(self, current_slot: int = None) -> int | None:
        """
        Возвращает следующий номер слота по кольцу для ротации (например, 1 -> 2 -> 3 -> 4 -> 1).
        """
        slots = sorted(self.list_slots().keys())
        if not slots:
            return None
        if len(slots) == 1:
            return slots[0]

        if current_slot is None:
            meta = self._load_metadata()
            current_slot = meta.get("active_slot")

        if current_slot in slots:
            idx = slots.index(current_slot)
            return slots[(idx + 1) % len(slots)]
        return slots[0]

    @staticmethod
    def restart_language_server() -> bool:
        """
        Мягко завершает процесс language_server.
        Electron (Antigravity 2.0) автоматически перезапускает его через 1 секунду
        с новым портом и новой сессией авторизации из Keychain.
        """
        try:
            if sys.platform == "darwin" or sys.platform.startswith("linux"):
                subprocess.run(
                    ["pkill", "-f", "language_server.*--standalone"],
                    capture_output=True,
                    check=False,
                )
            elif os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/IM", "language_server.exe"],
                    capture_output=True,
                    check=False,
                )
            return True
        except Exception:
            return False
