#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
          ANTIGRAVITY TOOLKIT — РУЧНАЯ СВЕРКА С UPSTREAM АНЛОКЕРОМ
================================================================================
Скрипт вызывается агентом (.agent) или разработчиком для ручной проверки
новых патчей, смещений и обновлений из репозитория AvenCores/open-antigravity-patcher.

В соответствии с политикой нулевых сетевых утечек приложения:
Сама программа НИКОГДА не проверяет обновления в фоне.
Синхронизация выполняется только вручную через git и .agent.
================================================================================
"""

import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from patcher.constants import VERSION, COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_RED, COLOR_BOLD, COLOR_RESET

UPSTREAM_URL = "https://github.com/AvenCores/open-antigravity-patcher.git"
UPSTREAM_REMOTE = "upstream"


def run_git(args: list[str]) -> tuple[int, str, str]:
    """Выполняет команду git и возвращает (code, stdout, stderr)."""
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def ensure_upstream_remote():
    """Проверяет наличие remote 'upstream', добавляет при отсутствии."""
    code, stdout, _ = run_git(["remote", "-v"])
    if UPSTREAM_REMOTE not in stdout:
        print(f"[*] Добавление remote '{UPSTREAM_REMOTE}': {UPSTREAM_URL}")
        run_git(["remote", "add", UPSTREAM_REMOTE, UPSTREAM_URL])
    else:
        print(f"[+] Git remote '{UPSTREAM_REMOTE}' настроен.")


def fetch_upstream():
    """Подтягивает обновления из upstream."""
    print(f"[*] Получение метаданных и тегов из {UPSTREAM_REMOTE}...")
    code, out, err = run_git(["fetch", UPSTREAM_REMOTE, "--tags"])
    if code != 0:
        print(f"[-] Предупреждение при fetch: {err}")
    else:
        print("[+] Данные upstream успешно получены.")


def check_updates():
    print("=" * 74)
    print(" 🔍 ПРОВЕРКА ОБНОВЛЕНИЙ И СМЕЩЕНИЙ UPSTREAM (РУЧНОЙ РЕЖИМ ЧЕРЕЗ .AGENT)")
    print("=" * 74)
    print(f"Текущая версия локального Toolkit: v{VERSION}")

    ensure_upstream_remote()
    fetch_upstream()

    # 1. Проверяем теги upstream
    code, tags_out, _ = run_git(["tag", "-l", "V*", "--sort=-v:refname"])
    tags = [t for t in tags_out.split("\n") if t.strip()]
    latest_upstream_tag = tags[0] if tags else "неизвестно"
    print(f"Последний релизный тег в upstream: {latest_upstream_tag}")

    clean_cur = VERSION.lstrip("vV")
    clean_up = latest_upstream_tag.lstrip("vV")

    # 2. Получаем 5 последних коммитов upstream, затрагивающих код патчера
    code, commits_out, _ = run_git([
        "log", f"{UPSTREAM_REMOTE}/main", "-n", "8",
        "--pretty=format:%h %ad | %s", "--date=short",
        "--", "source/patcher/"
    ])

    print("-" * 74)
    if clean_cur == clean_up:
        print(f"✅ Базовые версии совпадают (локальная v{VERSION} == upstream {latest_upstream_tag}).")
    else:
        print(f"⚠️  Версия upstream ({latest_upstream_tag}) отличается от локальной (v{VERSION})!")

    if commits_out:
        print("\n📦 Последние коммиты в upstream (ядро патчера source/patcher/):")
        for line in commits_out.split("\n"):
            print(f"   • {line}")

    print("\n📋 Протокол синхронизации через .agent:")
    print("   1. Подробный просмотр изменений файла в upstream:")
    print(f"      git show {UPSTREAM_REMOTE}/main:source/patcher/manager/patcher.py")
    print("   2. Сравнение с локальным файлом ядра:")
    print(f"      git diff HEAD -- patcher/manager/patcher.py")
    print("   3. Ручной перенос сигнатур в patcher/ без затирания русской локализации и GUI.")
    print("   4. Все детали описаны в файле: .agent/workflows/sync_unlocker.md")
    print("=" * 74)


if __name__ == "__main__":
    check_updates()
