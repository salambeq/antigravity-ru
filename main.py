#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
           ANTIGRAVITY TOOLKIT — ЦЕНТР УПРАВЛЕНИЯ И ЛОКАЛИЗАЦИИ
================================================================================
Интерактивная консольная утилита для:
  • Полного снятия региональных ограничений (Antigravity 2.0, IDE, CLI, VS Code)
  • Полной русской локализации интерфейса и ядра
  • Мгновенного переключения языка интерфейса (RU <-> EN)
  • Безопасного восстановления оригинальных файлов
  • Установки русскоязычных стандартов разработки и навыка i18n
================================================================================
"""

import os
import sys
import shutil
import subprocess
import json

# Добавляем текущую директорию в sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from patcher.constants import (
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_BOLD,
    COLOR_DIM,
    COLOR_WHITE,
    COLOR_RESET,
    DOWNLOAD_URL,
    VERSION,
)
from patcher.utils.console import (
    color,
    link,
    clear_screen,
    print_banner,
    print_menu_section,
    print_menu_row,
    print_menu_divider,
    print_menu_footer,
    info,
    hint,
    ok,
    warn,
    err,
    cancel,
    step,
)
from patcher.utils.file import file_size, format_bytes, resign_macos_binary, resign_macos_bundle
from patcher.cli import pause, confirmed, prompt_yn

# Импорты подсистем поиска и патчинга
from patcher.manager.discovery import find_manager_binary, resolve_manager_path, get_antigravity_version
from patcher.manager.patcher import is_already_patched as is_mgr_patched, do_patch_manager, do_restore_manager

from patcher.ide.discovery import find_install_root, find_main_js, get_ag_version, resolve_target_path
from patcher.ide.patcher import is_already_patched as is_ide_patched, do_patch as do_patch_ide, do_restore as do_restore_ide

from patcher.agy.discovery import find_agy_binary, resolve_agy_path
from patcher.agy.patcher import is_already_patched as is_agy_patched, do_patch_agy, do_restore_agy

from patcher.vscode.discovery import find_extension_js, find_gemini_antigravity_binary, resolve_extension_path
from patcher.vscode.patcher import is_already_patched as is_vscode_patched, do_patch_vscode, do_restore_vscode

from patcher.localization import (
    do_localize,
    do_switch_language,
    do_install_rules,
    is_already_localized,
    get_resources_path,
)
from patcher.accounts import AccountManager, QuotaRotator
from patcher.backup import BackupManager


def _kv(label, value_text, value_color):
    """Форматированный вывод строки состояния с фиксированным отступом."""
    print(f"      {label:<18} {color(value_text, value_color)}")


def get_all_targets():
    """Находит пути ко всем установленным компонентам Antigravity."""
    mgr_bin = find_manager_binary()
    ide_js = ""
    ide_root = find_install_root()
    if ide_root:
        ide_js = find_main_js(ide_root)

    agy_bin = find_agy_binary()
    vscode_js = find_extension_js()
    vscode_agy = find_gemini_antigravity_binary()

    return {
        "manager": mgr_bin,
        "ide": ide_js,
        "agy": agy_bin,
        "vscode_js": vscode_js,
        "vscode_agy": vscode_agy,
    }


def get_system_status_json():
    """Возвращает структурированный статус всех компонентов и аккаунтов в формате JSON."""
    targets = get_all_targets()
    mgr = targets["manager"]
    ide = targets["ide"]
    agy = targets["agy"]
    vs_js = targets["vscode_js"]
    vs_agy = targets["vscode_agy"]

    mgr_unlocked = is_mgr_patched(mgr) if (mgr and os.path.isfile(mgr)) else False
    mgr_localized = is_already_localized(mgr) if (mgr and os.path.isfile(mgr)) else False
    mgr_version = get_antigravity_version(mgr) if (mgr and os.path.isfile(mgr)) else None

    ide_patched = False
    ide_version = None
    if ide and os.path.isfile(ide):
        try:
            ver, _ = get_ag_version(ide)
            ide_version = ver
            with open(ide, "r", encoding="utf-8") as f:
                ide_patched = is_ide_patched(f.read())
        except Exception:
            pass

    agy_patched = is_agy_patched(agy) if (agy and os.path.isfile(agy)) else False

    vs_js_patched = False
    if vs_js and os.path.isfile(vs_js):
        try:
            with open(vs_js, "r", encoding="utf-8") as f:
                vs_js_patched = is_vscode_patched(f.read())
        except Exception:
            pass
    vs_agy_patched = is_agy_patched(vs_agy) if (vs_agy and os.path.isfile(vs_agy)) else False

    cur_acc = {"authenticated": False, "email": None, "name": None, "slot": None}
    slots_dict = {}
    try:
        ac_mgr = AccountManager()
        raw_slots = ac_mgr.list_slots()
        cur = ac_mgr.get_current_account_info()
        meta = ac_mgr._load_metadata()
        cur_acc = {
            "authenticated": cur.get("authenticated", False),
            "email": cur.get("email"),
            "name": cur.get("name"),
            "slot": meta.get("active_slot"),
        }
        for k, v in raw_slots.items():
            slots_dict[str(k)] = v
    except Exception:
        pass

    backups_data = {"chat_count": 0, "list": []}
    try:
        bm = BackupManager()
        backups_data = {
            "chat_count": bm.get_conversation_count(),
            "list": bm.list_backups(),
        }
    except Exception:
        pass

    return {
        "manager": {
            "path": mgr or "",
            "exists": bool(mgr and os.path.isfile(mgr)),
            "version": mgr_version or "",
            "unlocked": mgr_unlocked,
            "localized": mgr_localized,
        },
        "ide": {
            "path": ide or "",
            "exists": bool(ide and os.path.isfile(ide)),
            "version": ide_version or "",
            "unlocked": ide_patched,
        },
        "agy": {
            "path": agy or "",
            "exists": bool(agy and os.path.isfile(agy)),
            "unlocked": agy_patched,
        },
        "vscode": {
            "js_path": vs_js or "",
            "js_exists": bool(vs_js and os.path.isfile(vs_js)),
            "js_patched": vs_js_patched,
            "agy_path": vs_agy or "",
            "agy_exists": bool(vs_agy and os.path.isfile(vs_agy)),
            "agy_patched": vs_agy_patched,
        },
        "accounts": {
            "current": cur_acc,
            "slots": slots_dict,
        },
        "backups": backups_data,
    }


def print_status_dashboard(targets):
    """Отображает красивый статус всех компонентов."""
    print_menu_section("ДИАГНОСТИКА И СТАТУС КОМПОНЕНТОВ")

    # 1. Antigravity 2.0 (Manager)
    mgr = targets["manager"]
    print(f"  {color('● Antigravity 2.0 (Десктопное приложение):', COLOR_BOLD, COLOR_WHITE)}")
    if mgr and os.path.isfile(mgr):
        _kv("Путь:", mgr, COLOR_CYAN)
        ver = get_antigravity_version(mgr)
        _kv("Версия:", ver if ver else "Не определена", COLOR_GREEN if ver else COLOR_YELLOW)
        
        # Статус разблокировки
        unlocked = is_mgr_patched(mgr)
        _kv("Регион (Auth):", "✅ РАЗБЛОКИРОВАН (hasValidAuth=true)" if unlocked else "⚠️ Ограничен (Оригинальный)", 
            COLOR_GREEN if unlocked else COLOR_YELLOW)
        
        # Статус локализации
        localized = is_already_localized(mgr)
        _kv("Интерфейс:", "🇷🇺 РУССКИЙ ЯЗЫК (Локализован)" if localized else "🌐 АНГЛИЙСКИЙ (Оригинал)", 
            COLOR_GREEN if localized else COLOR_CYAN)
    else:
        _kv("Статус:", "Не обнаружен в стандартных директориях", COLOR_YELLOW)
    print()

    # 2. Antigravity IDE
    ide = targets["ide"]
    print(f"  {color('● Antigravity IDE (Редактор на базе VS Code):', COLOR_BOLD, COLOR_WHITE)}")
    if ide and os.path.isfile(ide):
        _kv("Путь:", ide, COLOR_CYAN)
        ver, _ = get_ag_version(ide)
        _kv("Версия:", ver if ver else "Не определена", COLOR_GREEN if ver else COLOR_YELLOW)
        try:
            with open(ide, "r", encoding="utf-8") as f:
                content = f.read()
            patched = is_ide_patched(content)
            _kv("Регион:", "✅ РАЗБЛОКИРОВАН (isGoogleInternal=true)" if patched else "⚠️ Ограничен (Оригинальный)",
                COLOR_GREEN if patched else COLOR_YELLOW)
        except Exception:
            _kv("Регион:", "Ошибка чтения", COLOR_RED)
    else:
        _kv("Статус:", "Не установлен (или путь не найден)", COLOR_DIM)
    print()

    # 3. Antigravity CLI (agy)
    agy = targets["agy"]
    print(f"  {color('● Antigravity CLI (Консольная утилита agy):', COLOR_BOLD, COLOR_WHITE)}")
    if agy and os.path.isfile(agy):
        _kv("Путь:", agy, COLOR_CYAN)
        patched = is_agy_patched(agy)
        _kv("Регион:", "✅ РАЗБЛОКИРОВАН (bypass eligibility)" if patched else "⚠️ Ограничен",
            COLOR_GREEN if patched else COLOR_YELLOW)
    else:
        _kv("Статус:", "Не установлена в PATH", COLOR_DIM)
    print()

    # 4. VS Code Extension
    vs_js = targets["vscode_js"]
    vs_agy = targets["vscode_agy"]
    print(f"  {color('● Расширение для VS Code (google.google-antigravity):', COLOR_BOLD, COLOR_WHITE)}")
    if vs_js and os.path.isfile(vs_js):
        _kv("Extension JS:", vs_js, COLOR_CYAN)
        try:
            with open(vs_js, "r", encoding="utf-8") as f:
                patched = is_vscode_patched(f.read())
            _kv("Патч JS:", "✅ Применен" if patched else "⚠️ Не применен", COLOR_GREEN if patched else COLOR_YELLOW)
        except Exception:
            pass
        if vs_agy and os.path.isfile(vs_agy):
            _kv("Бинарник agy:", vs_agy, COLOR_CYAN)
            agy_p = is_agy_patched(vs_agy)
            _kv("Патч agy:", "✅ Разблокирован" if agy_p else "⚠️ Не разблокирован", COLOR_GREEN if agy_p else COLOR_YELLOW)
    else:
        _kv("Статус:", "Не найдено в каталоге расширений VS Code", COLOR_DIM)
    print()

    # 5. Мультиаккаунт и квоты
    print(f"  {color('● Управление аккаунтами Google (Квоты):', COLOR_BOLD, COLOR_WHITE)}")
    try:
        ac_mgr = AccountManager()
        slots = ac_mgr.list_slots()
        cur = ac_mgr.get_current_account_info()
        meta = ac_mgr._load_metadata()
        act_slot = meta.get("active_slot")

        if cur.get("email"):
            slot_note = f" (Слот #{act_slot})" if act_slot else ""
            _kv("Активный аккаунт:", f"{cur['email']}{slot_note}", COLOR_GREEN)
        elif cur.get("authenticated"):
            _kv("Активный аккаунт:", "Авторизован в Antigravity", COLOR_GREEN)
        else:
            _kv("Активный аккаунт:", "Не авторизован", COLOR_YELLOW)

        if slots:
            slots_desc = ", ".join([f"#{k}: {v['email']}" for k, v in sorted(slots.items())])
            _kv("Сохранено слотов:", f"{len(slots)} ({slots_desc})", COLOR_CYAN)
        else:
            _kv("Сохранено слотов:", "0 (Сохраните аккаунты в меню [9])", COLOR_DIM)
    except Exception as e:
        _kv("Статус аккаунтов:", f"Ошибка: {e}", COLOR_RED)


def action_all_in_one(targets, interactive=True):
    """Выполняет комплексное снятие ограничений и полную русскую локализацию."""
    clear_screen()
    print_banner()
    step("⚡ ЗАПУСК КОМПЛЕКСНОЙ УСТАНОВКИ «ВСЁ В ОДИН КЛИК»")
    print()

    if interactive:
        warn("⚠️  ВНИМАНИЕ: Перед началом операций рекомендуется закрыть Antigravity.")
        warn("   Все оригинальные файлы будут защищены резервными копиями.")
        if not confirmed("   Вы уверены, что хотите продолжить?"):
            cancel("Операция отменена пользователем.")
            pause()
            return

    mgr = targets["manager"]
    if not mgr or not os.path.isfile(mgr):
        err("Antigravity 2.0 не найден. Проверьте установку программы.")
        if interactive:
            pause()
        return

    # 1. Локализация Antigravity 2.0 (app.asar + language_server)
    info("[1/4] Применение русской локализации интерфейса и ядра...")
    if not do_localize(mgr):
        err("Локализация завершилась с ошибкой.")
        pause()
        return
    ok("Русская локализация успешно применена!")

    # 2. Снятие региональных ограничений с Antigravity 2.0
    info("[2/4] Проверка и снятие региональных ограничений Antigravity 2.0...")
    if not is_mgr_patched(mgr):
        do_patch_manager(mgr)
    else:
        ok("Antigravity 2.0 уже разблокирован!")

    # 3. Разблокировка IDE, CLI и VS Code (если установлены)
    info("[3/4] Проверка дополнительных компонентов (IDE, CLI, VS Code)...")
    if targets["ide"] and os.path.isfile(targets["ide"]):
        try:
            with open(targets["ide"], "r", encoding="utf-8") as f:
                if not is_ide_patched(f.read()):
                    do_patch_ide(targets["ide"])
                else:
                    ok("Antigravity IDE уже разблокирован.")
        except Exception as e:
            warn(f"Не удалось пропатчить Antigravity IDE: {e}")

    if targets["agy"] and os.path.isfile(targets["agy"]):
        try:
            if not is_agy_patched(targets["agy"]):
                do_patch_agy(targets["agy"])
            else:
                ok("Antigravity CLI (agy) уже разблокирован.")
        except Exception as e:
            warn(f"Не удалось пропатчить Antigravity CLI: {e}")

    if targets["vscode_js"] and os.path.isfile(targets["vscode_js"]):
        try:
            from patcher.cli import do_patch_vscode_flow
            do_patch_vscode_flow(targets["vscode_js"], targets["vscode_agy"])
        except Exception as e:
            warn(f"Не удалось пропатчить VS Code расширение: {e}")

    # 4. Установка русскоязычных правил разработки и навыка i18n
    info("[4/4] Установка глобальных правил разработки и навыка i18n...")
    do_install_rules()

    print()
    ok("🎉 ВСЕ ОПЕРАЦИИ УСПЕШНО ЗАВЕРШЕНЫ!")
    hint("Пожалуйста, перезапустите Antigravity, чтобы увидеть изменения.")
    if interactive:
        pause()


def action_localize_ui(targets, interactive=True):
    """Применение только русской локализации."""
    clear_screen()
    print_banner()
    step("🇷🇺 УСТАНОВКА РУССКОЙ ЛОКАЛИЗАЦИИ ИНТЕРФЕЙСА")
    print()

    if interactive:
        warn("⚠️  ВНИМАНИЕ: Будет пересобран app.asar и обновлен language_server.")
        warn("   Рекомендуется закрыть Antigravity перед началом.")
        if not confirmed("   Вы уверены, что хотите продолжить?"):
            cancel("Операция отменена пользователем.")
            pause()
            return

    mgr = targets["manager"]
    if not mgr or not os.path.isfile(mgr):
        err("Antigravity 2.0 не найден.")
        if interactive:
            pause()
        return

    if do_localize(mgr):
        ok("Локализация успешно применена! Перезапустите программу.")
    else:
        err("Не удалось применить локализацию.")
    if interactive:
        pause()


def action_unlock_all(targets, interactive=True):
    """Снятие региональных ограничений со всех найденных компонентов."""
    clear_screen()
    print_banner()
    step("🔓 СНЯТИЕ РЕГИОНАЛЬНЫХ ОГРАНИЧЕНИЙ (REGION UNLOCK)")
    print()

    if interactive:
        warn("⚠️  ВНИМАНИЕ: Будут сняты региональные ограничения (патч бинарных файлов и скриптов).")
        warn("   Рекомендуется закрыть Antigravity перед началом.")
        if not confirmed("   Вы уверены, что хотите продолжить?"):
            cancel("Операция отменена пользователем.")
            pause()
            return

    # Antigravity 2.0
    if targets["manager"] and os.path.isfile(targets["manager"]):
        info("Разблокировка Antigravity 2.0 (language_server)...")
        do_patch_manager(targets["manager"])
    else:
        warn("Antigravity 2.0 не найден, пропуск.")

    # Antigravity IDE
    if targets["ide"] and os.path.isfile(targets["ide"]):
        info("Разблокировка Antigravity IDE (main.js)...")
        do_patch_ide(targets["ide"])
    else:
        warn("Antigravity IDE не найден, пропуск.")

    # Antigravity CLI
    if targets["agy"] and os.path.isfile(targets["agy"]):
        info("Разблокировка Antigravity CLI (agy)...")
        do_patch_agy(targets["agy"])
    else:
        warn("Antigravity CLI не найден, пропуск.")

    # VS Code
    if targets["vscode_js"] and os.path.isfile(targets["vscode_js"]):
        info("Разблокировка расширения VS Code...")
        from patcher.cli import do_patch_vscode_flow
        do_patch_vscode_flow(targets["vscode_js"], targets["vscode_agy"])
    else:
        warn("VS Code расширение не найдено, пропуск.")

    ok("Операция разблокировки завершена!")
    if interactive:
        pause()


def action_switch_language(targets):
    """Переключение языка интерфейса."""
    clear_screen()
    print_banner()
    step("🌐 ПЕРЕКЛЮЧЕНИЕ ЯЗЫКА ИНТЕРФЕЙСА (RU <-> EN)")
    print()

    mgr = targets["manager"]
    if not mgr or not os.path.isfile(mgr):
        err("Antigravity 2.0 не найден.")
        pause()
        return

    localized = is_already_localized(mgr)
    current = "Русский (RU)" if localized else "Английский (EN)"
    info(f"Текущий активный язык: {color(current, COLOR_CYAN)}")
    print()
    print_menu_row("1", "Включить РУССКИЙ язык (RU)", "Локализованный интерфейс и ядро", COLOR_GREEN)
    print_menu_row("2", "Включить АНГЛИЙСКИЙ язык (EN)", "Оригинальный интерфейс", COLOR_YELLOW)
    print()
    print_menu_row("0", "Назад", "", COLOR_RED)
    print()

    choice = input(color("  Выберите вариант > ", COLOR_CYAN, COLOR_BOLD)).strip()
    if choice == "1":
        do_switch_language("ru", mgr)
    elif choice == "2":
        do_switch_language("en", mgr)
    pause()


def action_restore_all(targets, interactive=True):
    """Восстановление оригинальных файлов для всех компонентов."""
    clear_screen()
    print_banner()
    step("⏪ ВОССТАНОВЛЕНИЕ ОРИГИНАЛЬНЫХ ФАЙЛОВ")
    print()
    warn("Внимание: это действие вернет все компоненты к оригинальному заводскому состоянию.")
    if interactive and not confirmed("Вы уверены, что хотите восстановить все оригинальные файлы?"):
        cancel("Восстановление отменено.")
        pause()
        return

    # 1. Antigravity 2.0
    res_path = get_resources_path(targets["manager"])
    if res_path and os.path.isdir(res_path):
        info("Восстановление Antigravity 2.0...")
        # app.asar
        orig_asar = os.path.join(res_path, "app.asar.orig")
        dest_asar = os.path.join(res_path, "app.asar")
        if os.path.exists(orig_asar):
            shutil.copyfile(orig_asar, dest_asar)
            ok("Восстановлен оригинальный app.asar")

        # language_server
        bin_name = "language_server.exe" if os.name == "nt" else "language_server"
        orig_bin = os.path.join(res_path, "bin", bin_name + ".orig")
        dest_bin = os.path.join(res_path, "bin", bin_name)
        if os.path.exists(orig_bin):
            shutil.copyfile(orig_bin, dest_bin)
            os.chmod(dest_bin, 0o755)
            if sys.platform == "darwin":
                resign_macos_binary(dest_bin)
            ok("Восстановлен оригинальный language_server")
        elif targets["manager"]:
            do_restore_manager(targets["manager"])

    # 2. Antigravity IDE
    if targets["ide"] and os.path.isfile(targets["ide"]):
        info("Восстановление Antigravity IDE...")
        do_restore_ide(targets["ide"])

    # 3. Antigravity CLI
    if targets["agy"] and os.path.isfile(targets["agy"]):
        info("Восстановление Antigravity CLI...")
        do_restore_agy(targets["agy"])

    # 4. VS Code
    if targets["vscode_js"] and os.path.isfile(targets["vscode_js"]):
        info("Восстановление расширения VS Code...")
        do_restore_vscode(targets["vscode_js"])

    ok("Все компоненты успешно возвращены к оригинальному состоянию!")
    if interactive:
        pause()


def action_diagnostics(targets, interactive=True):
    """Подробная диагностика целостности и прав доступа."""
    clear_screen()
    print_banner()
    step("🔍 ПОДРОБНАЯ ДИАГНОСТИКА СИСТЕМЫ И ПРОВЕРКА ЦЕЛОСТНОСТИ")
    print()

    # Проверка Python и модулей
    print(f"  {color('● Окружение Python:', COLOR_BOLD, COLOR_WHITE)}")
    _kv("Версия Python:", sys.version.split()[0], COLOR_GREEN)
    _kv("Платформа:", sys.platform, COLOR_CYAN)
    
    npx = shutil.which("npx")
    node = shutil.which("node")
    _kv("Node.js:", node if node else "Не установлен (используется готовый asar)", COLOR_GREEN if node else COLOR_YELLOW)
    _kv("NPX:", npx if npx else "Не установлен", COLOR_GREEN if npx else COLOR_YELLOW)
    print()

    # Проверка файлов Antigravity 2.0
    print(f"  {color('● Целостность файлов Antigravity 2.0:', COLOR_BOLD, COLOR_WHITE)}")
    mgr = targets["manager"]
    if mgr and os.path.isfile(mgr):
        _kv("Бинарник:", f"{format_bytes(file_size(mgr))} (OK)", COLOR_GREEN)
        if sys.platform == "darwin":
            res = subprocess.run(["codesign", "-v", mgr], capture_output=True, text=True)
            _kv("Код-подпись:", "Валидна (OK)" if res.returncode == 0 else f"Предупреждение: {res.stderr.strip()}", 
                COLOR_GREEN if res.returncode == 0 else COLOR_YELLOW)
        
        # Проверка запуска --stamp
        try:
            res_stamp = subprocess.run([mgr, "--stamp"], capture_output=True, text=True, timeout=5)
            if res_stamp.returncode == 0:
                first_line = res_stamp.stdout.strip().split("\n")[0]
                _kv("Запуск бинарника:", f"Успешно ({first_line})", COLOR_GREEN)
            else:
                _kv("Запуск бинарника:", f"Код возврата {res_stamp.returncode}", COLOR_RED)
        except Exception as e:
            _kv("Запуск бинарника:", f"Ошибка: {e}", COLOR_RED)
    else:
        _kv("Бинарник:", "Не найден", COLOR_RED)

    res_path = get_resources_path(mgr)
    if res_path:
        asar_p = os.path.join(res_path, "app.asar")
        if os.path.isfile(asar_p):
            _kv("app.asar:", f"{format_bytes(file_size(asar_p))} (OK)", COLOR_GREEN)
        else:
            _kv("app.asar:", "Не найден", COLOR_RED)

    print()
    if interactive:
        pause()


def action_custom_menu(targets):
    """Выборочное меню для опытных пользователей."""
    while True:
        clear_screen()
        print_banner()
        print_menu_section("ИНДИВИДУАЛЬНОЕ УПРАВЛЕНИЕ КОМПОНЕНТАМИ")
        print()
        print_menu_row("1", "Патч Antigravity IDE", "Снятие ограничений с main.js", COLOR_GREEN)
        print_menu_row("2", "Откат Antigravity IDE", "Восстановление main.js из бэкапа", COLOR_YELLOW)
        print_menu_divider()
        print_menu_row("3", "Патч Antigravity 2.0", "Снятие ограничений с language_server", COLOR_GREEN)
        print_menu_row("4", "Откат Antigravity 2.0", "Восстановление language_server из бэкапа", COLOR_YELLOW)
        print_menu_divider()
        print_menu_row("5", "Патч Antigravity CLI", "Снятие ограничений с agy", COLOR_GREEN)
        print_menu_row("6", "Откат Antigravity CLI", "Восстановление agy из бэкапа", COLOR_YELLOW)
        print_menu_divider()
        print_menu_row("7", "Патч VS Code Extension", "Патч extension.js + agy", COLOR_GREEN)
        print_menu_row("8", "Откат VS Code Extension", "Восстановление расширения", COLOR_YELLOW)
        print()
        print_menu_row("0", "Вернуться в главное меню", "", COLOR_RED)
        print()

        c = input(color("  Выберите вариант > ", COLOR_CYAN, COLOR_BOLD)).strip()
        if c == "0":
            break
        elif c == "1":
            if targets["ide"]:
                do_patch_ide(targets["ide"])
            else:
                warn("Путь к IDE не задан.")
            pause()
        elif c == "2":
            if targets["ide"]:
                do_restore_ide(targets["ide"])
            else:
                warn("Путь к IDE не задан.")
            pause()
        elif c == "3":
            if targets["manager"]:
                do_patch_manager(targets["manager"])
            else:
                warn("Путь к Antigravity 2.0 не задан.")
            pause()
        elif c == "4":
            if targets["manager"]:
                do_restore_manager(targets["manager"])
            else:
                warn("Путь к Antigravity 2.0 не задан.")
            pause()
        elif c == "5":
            if targets["agy"]:
                do_patch_agy(targets["agy"])
            else:
                warn("Путь к agy не задан.")
            pause()
        elif c == "6":
            if targets["agy"]:
                do_restore_agy(targets["agy"])
            else:
                warn("Путь к agy не задан.")
            pause()
        elif c == "7":
            if targets["vscode_js"]:
                from patcher.cli import do_patch_vscode_flow
                do_patch_vscode_flow(targets["vscode_js"], targets["vscode_agy"])
            else:
                warn("Расширение VS Code не найдено.")
            pause()
        elif c == "8":
            if targets["vscode_js"]:
                do_restore_vscode(targets["vscode_js"])
            else:
                warn("Расширение VS Code не найдено.")
            pause()


def action_accounts_menu(targets=None):
    """Интерактивное меню управления аккаунтами и авто-ротацией квот."""
    mgr = AccountManager()
    import time
    while True:
        clear_screen()
        print_banner()
        print_menu_section("МУЛЬТИАККАУНТ И АВТО-РОТАЦИЯ КВОТ")
        print()

        cur = mgr.get_current_account_info()
        slots = mgr.list_slots()
        meta = mgr._load_metadata()
        active_slot = meta.get("active_slot")

        if cur.get("email"):
            print(f"  {color('Текущий авторизованный аккаунт:', COLOR_BOLD)} {color(cur['email'], COLOR_GREEN)}")
        elif cur.get("authenticated"):
            print(f"  {color('Текущий авторизованный аккаунт:', COLOR_BOLD)} {color('Авторизован в Antigravity', COLOR_GREEN)}")
        else:
            print(f"  {color('Текущий авторизованный аккаунт:', COLOR_BOLD)} {color('Не авторизован в Antigravity', COLOR_YELLOW)}")

        if active_slot and active_slot in slots:
            active_email = slots[active_slot]["email"]
            print(f"  {color('Текущий активный слот:', COLOR_BOLD)}        {color(f'Слот #{active_slot} ({active_email})', COLOR_CYAN)}")
        print()

        print_menu_row("1", "💾 Сохранить текущий аккаунт", "Привязать текущую авторизацию к слоту (1..4)", COLOR_GREEN)
        print_menu_row("2", "🔄 Переключить слот", "Быстро переключиться на аккаунт 1, 2, 3 или 4", COLOR_CYAN)
        print_menu_row("3", "📋 Список всех слотов", "Просмотр сохранённых аккаунтов и метаданных", COLOR_CYAN)
        print_menu_row("4", "⚡ Запустить авто-ротатор", "Авто-смена аккаунта в реальном времени при ошибках квот", COLOR_GREEN)
        print_menu_row("5", "❌ Удалить слот", "Удалить сохранённый профиль аккаунта", COLOR_YELLOW)
        print()
        print_menu_row("0", "Вернуться в главное меню", "", COLOR_RED)
        print()

        c = input(color("  Выберите вариант > ", COLOR_CYAN, COLOR_BOLD)).strip()
        if c == "0":
            break
        elif c == "1":
            print()
            step("СОХРАНЕНИЕ ТЕКУЩЕГО АККАУНТА В СЛОТ")
            if not cur.get("authenticated"):
                err("В Antigravity нет активной авторизации. Сначала войдите в Google-аккаунт в приложении!")
                pause()
                continue
            s_num = input(color("  Введите номер слота (1-9) [по умолчанию 1] > ", COLOR_CYAN)).strip() or "1"
            try:
                s_int = int(s_num)
                success, msg = mgr.save_current_account(s_int)
                if success:
                    ok(msg)
                else:
                    err(msg)
            except ValueError:
                err("Номер слота должен быть числом.")
            pause()
        elif c == "2":
            print()
            step("ПЕРЕКЛЮЧЕНИЕ АККАУНТА")
            if not slots:
                warn("Пока нет сохранённых слотов. Сначала войдите в аккаунт и сохраните его (пункт 1).")
                pause()
                continue
            print("  Доступные слоты:")
            for k, v in sorted(slots.items()):
                is_act = " (активен)" if k == active_slot else ""
                print(f"    • Слот #{k}: {v['email']}{is_act}")
            s_num = input(color("\n  Введите номер слота для переключения > ", COLOR_CYAN)).strip()
            try:
                s_int = int(s_num)
                success, msg = mgr.switch_to_slot(s_int, restart_ls=True)
                if success:
                    ok(msg)
                    hint("language_server перезапущен. В течение 2-3 секунд Antigravity обновит квоту.")
                else:
                    err(msg)
            except ValueError:
                err("Номер слота должен быть числом.")
            pause()
        elif c == "3":
            print()
            step("СПИСОК СОХРАНЁННЫХ СЛОТОВ")
            if not slots:
                info("Нет сохранённых слотов.")
            else:
                for k, v in sorted(slots.items()):
                    active_mark = f" {color('[АКТИВЕН]', COLOR_BOLD, COLOR_GREEN)}" if k == active_slot else ""
                    print(f"  ● Слот #{k}:{active_mark}")
                    print(f"      Email:     {color(v['email'], COLOR_CYAN)}")
                    if v.get("name"):
                        print(f"      Имя:       {v['name']}")
                    if v.get("saved_at"):
                        t_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(v['saved_at']))
                        print(f"      Сохранён:  {t_str}")
                    print()
            pause()
        elif c == "4":
            print()
            step("ЗАПУСК АВТО-РОТАТОРА КВОТ")
            if len(slots) < 2:
                warn("Для авто-ротации рекомендуется сохранить как минимум 2 аккаунта.")
                if not prompt_yn("Продолжить запуск?"):
                    continue
            rotator = QuotaRotator()
            rotator.start_watch()
            pause()
        elif c == "5":
            print()
            step("УДАЛЕНИЕ СЛОТА")
            if not slots:
                info("Нет сохранённых слотов.")
                pause()
                continue
            s_num = input(color("  Введите номер слота для удаления > ", COLOR_CYAN)).strip()
            try:
                s_int = int(s_num)
                success, msg = mgr.delete_slot(s_int)
                if success:
                    ok(msg)
                else:
                    err(msg)
            except ValueError:
                err("Номер слота должен быть числом.")
            pause()


def action_backups_menu(targets=None):
    """Интерактивное управление резервными копиями чатов и данных Antigravity."""
    bm = BackupManager()
    while True:
        clear_screen()
        print_banner()
        print_menu_section("РЕЗЕРВНОЕ КОПИРОВАНИЕ И ВОССТАНОВЛЕНИЕ ДАННЫХ")
        print()

        chat_count = bm.get_conversation_count()
        print(f"  ● Состояние хранилища Antigravity:")
        _kv("Обнаружено диалогов:", f"{chat_count} шт.", COLOR_GREEN if chat_count > 0 else COLOR_YELLOW)
        _kv("Каталог бэкапов:", bm.backup_dir, COLOR_CYAN)
        print()

        backups = bm.list_backups()
        if backups:
            print(f"  {color('● Доступные резервные копии:', COLOR_BOLD, COLOR_WHITE)}")
            for idx, b in enumerate(backups[:8], 1):
                note_str = f" — {b['note']}" if b.get("note") else ""
                print(f"    [{idx}] {b['filename']} ({b['size_formatted']}, диалогов: {b['chat_count']}, дата: {b['created_at_iso']}){note_str}")
        else:
            print(f"  {color('● Доступные резервные копии:', COLOR_BOLD, COLOR_WHITE)}")
            print("    (Резервных копий пока нет)")
        print()

        print_menu_section("ДЕЙСТВИЯ С РЕЗЕРВНЫМИ КОПИЯМИ")
        print_menu_row("1", "Создать копию чатов", "Архивация диалогов, сессий, настроек и аккаунтов", COLOR_GREEN)
        print_menu_row("2", "Создать полную копию", "Включая логи и артефакты мозга (brain)", COLOR_CYAN)
        print_menu_row("3", "Восстановить из копии", "Восстановить чаты из выбранного архива", COLOR_YELLOW)
        print_menu_row("4", "Удалить старую копию", "Удалить архив из списка", COLOR_RED)
        print()
        print_menu_row("0", "Вернуться в главное меню", "", COLOR_RED)
        print()

        choice = input(color("  Выберите вариант > ", COLOR_CYAN, COLOR_BOLD)).strip()
        if choice == "0":
            break
        elif choice == "1":
            bm.create_backup(backup_type="chats", note="Ручной бэкап чатов")
            pause()
        elif choice == "2":
            warn("Полная копия может занять больше времени и места на диске.")
            if prompt_yn("Продолжить создание полной копии?", default=True):
                bm.create_backup(backup_type="full", note="Полный бэкап")
            pause()
        elif choice == "3":
            if not backups:
                warn("Нет доступных резервных копий.")
                pause()
                continue
            idx_str = input(color("  Введите номер копии для восстановления (1..N) > ", COLOR_CYAN)).strip()
            try:
                sel_idx = int(idx_str) - 1
                if 0 <= sel_idx < len(backups):
                    sel_b = backups[sel_idx]
                    warn(f"ВНИМАНИЕ: Восстановление перезапишет текущие диалоги копией от {sel_b['created_at_iso']}.")
                    if prompt_yn("Вы уверены, что хотите восстановить?", default=False):
                        bm.restore_backup(sel_b["path"])
                else:
                    err("Неверный номер.")
            except ValueError:
                err("Введите число.")
            pause()
        elif choice == "4":
            if not backups:
                warn("Нет резервных копий для удаления.")
                pause()
                continue
            idx_str = input(color("  Введите номер копии для удаления (1..N) > ", COLOR_RED)).strip()
            try:
                sel_idx = int(idx_str) - 1
                if 0 <= sel_idx < len(backups):
                    sel_b = backups[sel_idx]
                    if prompt_yn(f"Удалить {sel_b['filename']}?", default=False):
                        bm.delete_backup(sel_b["path"])
                else:
                    err("Неверный номер.")
            except ValueError:
                err("Введите число.")
            pause()


def main():
    # Обработка неинтерактивных флагов командной строки
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        targets = get_all_targets()
        if arg in ("--all", "-a"):
            action_all_in_one(targets, interactive=False)
            sys.exit(0)
        elif arg in ("--localize", "-l"):
            action_localize_ui(targets, interactive=False)
            sys.exit(0)
        elif arg in ("--unlock", "-u"):
            action_unlock_all(targets, interactive=False)
            sys.exit(0)
        elif arg in ("--switch", "-s") and len(sys.argv) > 2:
            do_switch_language(sys.argv[2].lower(), targets["manager"])
            sys.exit(0)
        elif arg in ("--restore", "-r"):
            action_restore_all(targets, interactive=False)
            sys.exit(0)
        elif arg in ("--diagnostics", "-d"):
            action_diagnostics(targets, interactive=False)
            sys.exit(0)
        elif arg in ("--accounts", "-ac"):
            mgr = AccountManager()
            slots = mgr.list_slots()
            cur = mgr.get_current_account_info()
            print("Текущий аккаунт:", cur.get("email") or "Не определен")
            print("Сохраненные слоты:")
            for k, v in sorted(slots.items()):
                print(f"  [{k}] {v['email']} {'(активен)' if v.get('is_active') else ''}")
            sys.exit(0)
        elif arg in ("--account-save", "--save-account") and len(sys.argv) > 2:
            try:
                slot_idx = int(sys.argv[2])
                mgr = AccountManager()
                success, msg = mgr.save_current_account(slot_idx)
                if success:
                    ok(msg)
                else:
                    err(msg)
            except ValueError:
                err("Номер слота должен быть числом.")
            sys.exit(0)
        elif arg in ("--account-switch", "--switch-account") and len(sys.argv) > 2:
            try:
                slot_idx = int(sys.argv[2])
                mgr = AccountManager()
                success, msg = mgr.switch_to_slot(slot_idx, restart_ls=True)
                if success:
                    ok(msg)
                else:
                    err(msg)
            except ValueError:
                err("Номер слота должен быть числом.")
            sys.exit(0)
        elif arg in ("--auto-rotate", "--rotate"):
            rotator = QuotaRotator()
            rotator.start_watch()
            sys.exit(0)
        elif arg in ("--backup-create", "-bc"):
            btype = sys.argv[2] if len(sys.argv) > 2 else "chats"
            bm = BackupManager()
            success, msg, manifest = bm.create_backup(backup_type=btype)
            sys.exit(0 if success else 1)
        elif arg in ("--backup-list", "-bl"):
            bm = BackupManager()
            blist = bm.list_backups()
            print(f"Резервных копий: {len(blist)}")
            for b in blist:
                print(f"  • {b['filename']} ({b['size_formatted']}, диалогов: {b['chat_count']}, дата: {b['created_at_iso']})")
            sys.exit(0)
        elif arg in ("--backup-restore", "-br") and len(sys.argv) > 2:
            target_f = sys.argv[2]
            bm = BackupManager()
            success, msg = bm.restore_backup(target_f)
            sys.exit(0 if success else 1)
        elif arg in ("--backup-delete", "-bd") and len(sys.argv) > 2:
            target_f = sys.argv[2]
            bm = BackupManager()
            success, msg = bm.delete_backup(target_f)
            sys.exit(0 if success else 1)
        elif arg in ("--json-status", "--status-json"):
            print(json.dumps(get_system_status_json(), ensure_ascii=False, indent=2))
            sys.exit(0)

    # Интерактивный цикл
    while True:
        try:
            clear_screen()
            print_banner()
            targets = get_all_targets()
            print_status_dashboard(targets)
            print()

            print_menu_section("ГЛАВНОЕ МЕНЮ ДЕЙСТВИЙ")
            print_menu_row("1", "⚡ Всё в один клик", "Разблокировать регион + Полная русская локализация + Правила", COLOR_GREEN)
            print_menu_row("2", "🇷🇺 Локализация интерфейса", "Применить русский перевод к Antigravity 2.0", COLOR_GREEN)
            print_menu_row("3", "🔓 Снять региональные ограничения", "Разблокировать Antigravity 2.0, IDE, CLI, VS Code", COLOR_GREEN)
            print_menu_row("4", "🌐 Переключить язык", "Мгновенное переключение RU <-> EN без пересборки", COLOR_CYAN)
            print_menu_row("5", "⏪ Восстановить оригиналы", "Безопасный откат всех патчей к заводскому состоянию", COLOR_YELLOW)
            print_menu_row("6", "🛠 Установить правила и навыки", "Русские стандарты разработки и навык i18n", COLOR_CYAN)
            print_menu_row("7", "🎯 Выборочные патчи", "Индивидуальное управление компонентами (IDE, CLI и т.д.)", COLOR_CYAN)
            print_menu_row("8", "🔍 Подробная диагностика", "Проверка подписей, прав, контрольных сумм и модулей", COLOR_CYAN)
            print_menu_row("9", "🔄 Мультиаккаунт и авто-ротация", "Смена 4-х Google-аккаунтов и авто-переключение при исчерпании квот", COLOR_GREEN)
            print_menu_row("10", "📦 Резервная копия чатов", "Архивация и восстановление диалогов (чтобы чаты не пропадали)", COLOR_CYAN)
            print()
            print_menu_row("0", "Выход", "Завершить работу с утилитой", COLOR_RED)
            print_menu_footer("Совет: все изменения обратимы — пункт [5] возвращает оригинальные файлы.")

            choice = input(color("\n  Выберите действие > ", COLOR_CYAN, COLOR_BOLD)).strip()
            if choice == "0":
                print("\n  До свидания!\n")
                break
            elif choice == "1":
                action_all_in_one(targets)
            elif choice == "2":
                action_localize_ui(targets)
            elif choice == "3":
                action_unlock_all(targets)
            elif choice == "4":
                action_switch_language(targets)
            elif choice == "5":
                action_restore_all(targets)
            elif choice == "6":
                clear_screen()
                print_banner()
                do_install_rules()
                pause()
            elif choice == "7":
                action_custom_menu(targets)
            elif choice == "8":
                action_diagnostics(targets)
            elif choice == "9":
                action_accounts_menu(targets)
            elif choice == "10":
                action_backups_menu(targets)

        except KeyboardInterrupt:
            print("\n\n  Прервано пользователем. Выход.\n")
            break


if __name__ == "__main__":
    main()
