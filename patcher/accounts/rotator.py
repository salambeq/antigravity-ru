#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демон автоматической ротации аккаунтов при исчерпании квот токенов.
Следит за журналом language_server.log и мгновенно переключает на следующий слот.
"""

from __future__ import annotations

import os
import re
import sys
import time
import subprocess
from typing import Optional

from patcher.accounts.manager import AccountManager
from patcher.utils.console import (
    color,
    info,
    ok,
    warn,
    err,
    step,
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_BOLD,
)

# Сигнатуры ошибок исчерпания токенов / квот Google API
QUOTA_PATTERNS = [
    re.compile(r"QUOTA_EXHAUSTED", re.IGNORECASE),
    re.compile(r"RESOURCE_EXHAUSTED", re.IGNORECASE),
    re.compile(r"RATE_LIMIT_EXCEEDED", re.IGNORECASE),
    re.compile(r"status\s*429", re.IGNORECASE),
    re.compile(r"status:\s*429", re.IGNORECASE),
    re.compile(r"ARGON_LIMIT_REACHED", re.IGNORECASE),
    re.compile(r"exceeded your current quota", re.IGNORECASE),
    re.compile(r"ResourceExhausted", re.IGNORECASE),
    re.compile(r"Too many requests", re.IGNORECASE),
]


def get_default_log_path() -> str:
    """Возвращает путь к лог-файлу language_server в зависимости от ОС."""
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Logs", "Antigravity", "language_server.log")
    elif os.name == "nt":
        appdata = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
        return os.path.join(appdata, "Antigravity", "logs", "language_server.log")
    else:
        # Linux
        cfg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
        return os.path.join(cfg, "antigravity", "logs", "language_server.log")


def send_system_notification(title: str, message: str):
    """Отправляет нативное уведомление на рабочий стол."""
    try:
        if sys.platform == "darwin":
            # Экранируем кавычки
            safe_title = title.replace('"', '\\"')
            safe_msg = message.replace('"', '\\"')
            script = f'display notification "{safe_msg}" with title "{safe_title}" sound name "Glass"'
            subprocess.run(["osascript", "-e", script], capture_output=True, check=False)
        elif sys.platform.startswith("linux"):
            subprocess.run(["notify-send", title, message], capture_output=True, check=False)
        elif os.name == "nt":
            # PowerShell Toast
            ps_script = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $toastXml = [xml] $template.GetXml()
            $toastXml.GetElementsByTagName('text')[0].AppendChild($toastXml.CreateTextNode('{title}')) > $null
            $toastXml.GetElementsByTagName('text')[1].AppendChild($toastXml.CreateTextNode('{message}')) > $null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Antigravity').Show($toast)
            """
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, check=False)
    except Exception:
        pass


class QuotaRotator:
    def __init__(self, log_path: Optional[str] = None, cooldown_seconds: int = 15):
        self.log_path = log_path or get_default_log_path()
        self.cooldown_seconds = cooldown_seconds
        self.manager = AccountManager()
        self.last_rotation_time = 0.0

    def check_line_for_quota_error(self, line: str) -> bool:
        """Проверяет, содержит ли строка лога ошибку исчерпания квоты."""
        for pattern in QUOTA_PATTERNS:
            if pattern.search(line):
                return True
        return False

    def trigger_rotation(self, reason: str = "Квота исчерпана") -> bool:
        """Выполняет переключение на следующий доступный аккаунт."""
        now = time.time()
        if now - self.last_rotation_time < self.cooldown_seconds:
            # Защита от дребезга при пачке одновременных ошибок
            return False

        slots = self.manager.list_slots()
        if len(slots) < 2:
            warn(f"[{time.strftime('%H:%M:%S')}] Обнаружена ошибка квоты, но сохранено меньше 2-х слотов. Ротация невозможна.")
            send_system_notification(
                "Antigravity: Внимание",
                "Квота исчерпана, но для автоматической ротации нужно минимум 2 сохранённых аккаунта.",
            )
            self.last_rotation_time = now
            return False

        meta = self.manager._load_metadata()
        active_slot = meta.get("active_slot")
        next_slot = self.manager.get_next_slot_number(active_slot)

        if not next_slot or next_slot == active_slot:
            return False

        next_info = slots.get(next_slot, {})
        next_email = next_info.get("email", f"Слот #{next_slot}")

        step(f"[{time.strftime('%H:%M:%S')}] 🔄 {reason}! Переключение: Слот #{active_slot} -> Слот #{next_slot} ({next_email})...")

        success, msg = self.manager.switch_to_slot(next_slot, restart_ls=True)
        if success:
            self.last_rotation_time = time.time()
            ok(f"[{time.strftime('%H:%M:%S')}] ✅ Успешно активирован {next_email} (Слот #{next_slot})!")
            send_system_notification(
                "Antigravity: Квота переключена",
                f"Квота исчерпана. Автоматически активирован слот #{next_slot}: {next_email}",
            )
            return True
        else:
            err(f"[{time.strftime('%H:%M:%S')}] ❌ Не удалось переключить слот: {msg}")
            return False

    def start_watch(self):
        """Запускает непрерывный мониторинг файла журнала."""
        slots = self.manager.list_slots()
        print(f"  {color('● Авто-ротатор квот Antigravity запущен', COLOR_BOLD, COLOR_GREEN)}")
        print(f"    • Файл логов:    {color(self.log_path, COLOR_CYAN)}")
        print(f"    • Доступно слотов: {color(str(len(slots)), COLOR_YELLOW)} {list(slots.keys())}")
        print(f"    • Cooldown:        {self.cooldown_seconds} сек.")
        print(f"    • Для остановки нажмите {color('Ctrl+C', COLOR_YELLOW)}")
        print("-" * 65)

        # Ожидаем появления файла, если он еще не создан
        while not os.path.isfile(self.log_path):
            info(f"Ожидание создания файла журнала {self.log_path}...")
            time.sleep(2)

        try:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                # Перемещаемся в конец файла, чтобы не реагировать на старые ошибки
                f.seek(0, os.SEEK_END)
                last_pos = f.tell()

                while True:
                    # Проверяем не был ли файл урезан (log rotate)
                    cur_size = os.path.getsize(self.log_path)
                    if cur_size < last_pos:
                        f.seek(0, os.SEEK_SET)

                    line = f.readline()
                    if line:
                        last_pos = f.tell()
                        if self.check_line_for_quota_error(line):
                            self.trigger_rotation(reason="Обнаружено исчерпание квоты в логах")
                    else:
                        time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n  {color('Авто-ротатор остановлен пользователем.', COLOR_YELLOW)}")
