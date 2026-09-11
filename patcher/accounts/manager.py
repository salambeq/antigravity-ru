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

from patcher.accounts.keychain import (
    read_current_token_raw,
    write_token_raw,
    decode_token_payload,
    encode_token_payload,
    fetch_google_account_info,
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

    def get_current_account_info(self) -> dict:
        """
        Возвращает данные текущего авторизованного в системе аккаунта.
        """
        raw = read_current_token_raw()
        if not raw:
            return {"authenticated": False, "email": None, "error": "Токен не найден в связке ключей"}

        payload = decode_token_payload(raw)
        tok = payload.get("token", {})
        access_token = tok.get("access_token", "")
        refresh_token = tok.get("refresh_token", "")

        account_info = {
            "authenticated": bool(access_token or refresh_token),
            "has_refresh_token": bool(refresh_token),
            "expiry": tok.get("expiry"),
            "email": None,
            "name": None,
            "raw": raw,
        }

        if access_token:
            google_info = fetch_google_account_info(access_token)
            if google_info.get("email"):
                account_info["email"] = google_info.get("email")
                account_info["name"] = google_info.get("name")

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
            "saved_at": int(time.time()),
            "raw_payload": cur["raw"],
        }

        try:
            with open(slot_path, "w", encoding="utf-8") as f:
                json.dump(slot_data, f, indent=2)
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

    def list_slots(self) -> dict:
        """
        Возвращает список всех сохранённых слотов с их статусом.
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
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        slots[slot_num] = {
                            "email": data.get("email", f"Слот #{slot_num}"),
                            "name": data.get("name", ""),
                            "saved_at": data.get("saved_at", 0),
                            "is_active": (slot_num == meta.get("active_slot")),
                        }
                    except Exception:
                        pass

        return slots

    def switch_to_slot(self, slot_num: int, restart_ls: bool = True) -> tuple[bool, str]:
        """
        Переключает текущий аккаунт Antigravity на указанный слот.
        Записывает токен в Keychain и мягко перезапускает language_server.
        """
        slot_path = self.get_slot_path(slot_num)
        if not os.path.isfile(slot_path):
            return False, f"Слот #{slot_num} не найден. Сначала сохраните в него аккаунт."

        try:
            with open(slot_path, "r", encoding="utf-8") as f:
                slot_data = json.load(f)
            raw = slot_data.get("raw_payload", "")
            if not raw:
                return False, f"В слоте #{slot_num} повреждены данные токена."

            # 1. Записываем в системную связку ключей
            if not write_token_raw(raw):
                return False, "Не удалось записать токен в системное хранилище (Keychain)."

            # 2. Обновляем метаданные активного слота
            meta = self._load_metadata()
            meta["active_slot"] = slot_num
            self._save_metadata(meta)

            email_str = slot_data.get("email", f"Слот #{slot_num}")

            # 3. Перезапускаем language_server при необходимости
            if restart_ls:
                self.restart_language_server()

            return True, f"Успешно переключено на {email_str} (Слот #{slot_num})!"
        except Exception as e:
            return False, f"Ошибка переключения слота: {e}"

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
