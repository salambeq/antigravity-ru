#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Мастер безопасного добавления/переключения Google-аккаунтов в Antigravity.
Реализует механизм Zero-Revocation (локальный сброс связки ключей БЕЗ сетевого отзыва токенов).
"""

import os
import sys
import time
import signal
import argparse

# Обеспечиваем доступ к модулям пакета patcher
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from patcher.accounts.manager import AccountManager
from patcher.utils.console import (
    color,
    info,
    ok,
    warn,
    err,
    step,
    hint,
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_BOLD,
)


def print_wizard_banner(target_slot: int):
    print()
    print(color("╔══════════════════════════════════════════════════════════════╗", COLOR_CYAN, COLOR_BOLD))
    print(color("║       МАСТЕР БЕЗОПАСНОГО ВХОДА В GOOGLE (ZERO-REVOCATION)    ║", COLOR_CYAN, COLOR_BOLD))
    print(color("╚══════════════════════════════════════════════════════════════╝", COLOR_CYAN, COLOR_BOLD))
    print(f"  Целевой слот: {color(f'Слот #{target_slot}', COLOR_GREEN, COLOR_BOLD)}")
    print(f"  Защита:       {color('100% Zero-Revocation (сетевой отзыв токенов ОТКЛЮЧЕН)', COLOR_GREEN)}")
    print(f"  Хранилище:    {color('macOS Keychain + ~/.gemini/accounts', COLOR_CYAN)}")
    print(f"  Таймаут:      {color('180 секунд (опрос каждые 2 сек.)', COLOR_CYAN)}")
    print(color("────────────────────────────────────────────────────────────────", COLOR_CYAN))
    print()


def run_add_account_wizard(target_slot: int = None):
    mgr = AccountManager()

    # Считываем текущую информацию
    slots = mgr.list_slots(auto_heal=False)
    meta = mgr._load_metadata()
    active_slot = meta.get("active_slot")
    cur_info = mgr.get_current_account_info()

    # Если слот не передан аргументом, находим первый свободный (или спрашиваем)
    if target_slot is None:
        first_free = None
        for s in range(1, 10):
            if s not in slots:
                first_free = s
                break
        if not first_free:
            first_free = max(slots.keys(), default=0) + 1

        print()
        step("ВЫБОР ЦЕЛЕВОГО СЛОТА ДЛЯ НОВОГО АККАУНТА")
        if slots:
            print("  Текущие сохранённые слоты:")
            for s_num, s_data in sorted(slots.items()):
                act_mark = f" {color('[АКТИВЕН СЕЙЧАС]', COLOR_GREEN, COLOR_BOLD)}" if s_num == active_slot else ""
                print(f"    • Слот #{s_num}: {color(s_data['email'], COLOR_CYAN)} ({s_data.get('name') or 'Без имени'}){act_mark}")
        else:
            info("Сохранённых слотов пока нет.")

        prompt_text = f"\n  Введите номер целевого слота [по умолчанию {first_free}] > "
        try:
            choice = input(color(prompt_text, COLOR_CYAN, COLOR_BOLD)).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Отмена операции.")
            sys.exit(0)

        if choice:
            try:
                target_slot = int(choice)
            except ValueError:
                err("Номер слота должен быть положительным числом.")
                sys.exit(1)
        else:
            target_slot = first_free

    if target_slot < 1:
        err("Номер слота должен быть положительным числом (1, 2, 3...).")
        sys.exit(1)

    print_wizard_banner(target_slot)

    # Обработчик прерывания (Ctrl+C) для безопасного отката
    def handle_interrupt(signum, frame):
        print()
        warn("\n  Получен сигнал отмены (Ctrl+C). Выполняется безопасный откат...")
        mgr.cancel_wizard()
        ok("  Предыдущая сессия успешно восстановлена в Keychain. Antigravity перезапущена.")
        sys.exit(130)

    signal.signal(signal.SIGINT, handle_interrupt)
    signal.signal(signal.SIGTERM, handle_interrupt)

    step("Шаг 1/4: Изоляция и бэкап текущей активной сессии")
    if cur_info.get("email"):
        info(f"Активная сессия: {cur_info['email']} (синхронизирована в слот #{active_slot or 1})")
    else:
        info("Активная сессия зафиксирована и зарезервирована перед сбросом.")

    step("Шаг 2/4: Локальный сброс связки ключей БЕЗ сетевого отзыва (Zero-Revocation)")
    info("Удаление токена исключительно из локального Keychain...")
    info("Сетевые запросы к oauth2.googleapis.com/revoke полностью исключены.")

    step("Шаг 3/4: Мягкий перезапуск Electron-клиента и language_server")
    info("Выполняется pkill -x Antigravity && pkill -f language_server...")
    info("Запуск open -a Antigravity...")

    step("Шаг 4/4: Фоновый захват нового токена (Wizard Polling)")
    hint("Перейдите в окно Antigravity и выполните «Войти через Google» в браузере.")
    hint("Для отмены и возврата к прежнему аккаунту нажмите Ctrl+C в любой момент.\n")

    spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start_time = time.time()
    timeout = 180
    poll_interval = 2.0

    # Запускаем подготовку мастера
    ok_prep, prep_msg = mgr.prepare_slot_wizard(target_slot)
    if not ok_prep:
        err(f"Ошибка подготовки мастера: {prep_msg}")
        sys.exit(1)

    tick_idx = 0
    completed_status = None

    while time.time() - start_time < timeout:
        time.sleep(poll_interval)
        elapsed = int(time.time() - start_time)
        remaining = max(0, timeout - elapsed)
        sp = spinner_chars[tick_idx % len(spinner_chars)]
        tick_idx += 1

        sys.stdout.write(
            f"\r  {color(sp, COLOR_CYAN, COLOR_BOLD)} Ожидание авторизации в браузере... "
            f"Прошло: {color(str(elapsed) + 'с', COLOR_YELLOW)} | "
            f"Осталось: {color(str(remaining) + 'с', COLOR_CYAN)}  "
        )
        sys.stdout.flush()

        st = mgr.check_wizard_status()
        if st.get("completed"):
            completed_status = st
            break

    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

    if completed_status and completed_status.get("completed"):
        print()
        ok("════════════════════════════════════════════════════════════════")
        ok(f"🎉 НОВЫЙ GOOGLE-АККАУНТ УСПЕШНО ДОБАВЛЕН И АВТОРИЗОВАН!")
        ok(f"  • Слот:      Слот #{completed_status.get('target_slot')}")
        ok(f"  • Email:     {completed_status.get('email')}")
        if completed_status.get("name"):
            ok(f"  • Профиль:   {completed_status.get('name')}")
        ok(f"  • Файл:      ~/.gemini/accounts/slots/slot_{completed_status.get('target_slot')}.json")
        ok(f"  • Метаданные: accounts_meta.json обновлен (активный слот #{completed_status.get('target_slot')})")
        ok("════════════════════════════════════════════════════════════════")
        print()
    else:
        print()
        warn(f"Время ожидания авторизации ({timeout} сек.) истекло без входа.")
        info("Выполняется автоматический откат к предыдущей сессии...")
        mgr.cancel_wizard()
        ok("Предыдущий аккаунт успешно восстановлен. Antigravity возвращена в рабочее состояние.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Безопасное добавление Google-аккаунта в Antigravity (Zero-Revocation мастер)."
    )
    parser.add_argument(
        "slot",
        type=int,
        nargs="?",
        default=None,
        help="Номер целевого слота (например: 1, 2, 3, 4)",
    )
    args = parser.parse_args()
    run_add_account_wizard(args.slot)


if __name__ == "__main__":
    main()
