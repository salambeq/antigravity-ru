import os
import sys
import shutil
import subprocess
from patcher.utils.console import ok, info, warn, err, step, color
from patcher.constants import COLOR_GREEN, COLOR_YELLOW, COLOR_CYAN

def get_resources_path(manager_path=None):
    if manager_path and os.path.exists(manager_path):
        return os.path.dirname(os.path.dirname(os.path.abspath(manager_path)))

    env_path = os.environ.get("ANTIGRAVITY_RESOURCES_PATH")
    if env_path and os.path.isdir(env_path):
        return env_path

    # Поиск через менеджер
    try:
        from patcher.manager.discovery import find_manager_binary
        mgr_bin = find_manager_binary()
        if mgr_bin and os.path.isfile(mgr_bin):
            return os.path.dirname(os.path.dirname(os.path.abspath(mgr_bin)))
    except Exception:
        pass

    # Стандартные пути
    if sys.platform == 'darwin':
        paths = ["/Applications/Antigravity.app/Contents/Resources"]
    elif sys.platform.startswith('linux'):
        paths = [
            "/opt/Antigravity/resources",
            "/usr/lib/antigravity/resources",
            os.path.expanduser("~/.local/share/antigravity/resources")
        ]
    elif sys.platform == 'win32':
        local_app = os.environ.get("LOCALAPPDATA", "")
        prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        paths = [
            os.path.join(local_app, "Programs", "Antigravity", "resources"),
            os.path.join(prog_files, "Antigravity", "resources")
        ]
    else:
        paths = []

    for p in paths:
        if os.path.isdir(p):
            return p
    return paths[0] if paths else None


def is_already_localized(manager_path=None):
    res_path = get_resources_path(manager_path)
    if not res_path:
        return False
    asar_path = os.path.join(res_path, "app.asar")
    if not os.path.exists(asar_path):
        return False
    try:
        with open(asar_path, "rb") as f:
            data = f.read()
        return "Новое окно".encode("utf-8") in data
    except Exception:
        return False


def do_localize(manager_path=None):
    step("Запуск полной русской локализации Antigravity...")
    res_path = get_resources_path(manager_path)
    if not res_path or not os.path.isdir(res_path):
        err(f"Каталог ресурсов Antigravity не найден: {res_path}")
        return False

    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Patch language_server
    info("1/3 Локализация ядра (language_server)...")
    try:
        from patcher.patcher_binary_worker import patch_language_server
        patch_language_server(res_path, script_dir)
        ok("Ядро language_server успешно локализовано!")
    except Exception as e:
        err(f"Ошибка при локализации language_server: {e}")
        return False

    # 2. Patch app.asar
    info("2/3 Локализация интерфейса Electron (app.asar)...")
    try:
        from patcher.patcher_asar_worker import patch_app_asar
        patch_app_asar(res_path, script_dir)
        ok("Интерфейс app.asar успешно локализован!")
    except Exception as e:
        err(f"Ошибка при локализации app.asar: {e}")
        return False

    # 3. Сохранение копий для быстрого переключения языков
    try:
        shutil.copyfile(os.path.join(res_path, "app.asar"), os.path.join(script_dir, "app.asar.ru"))
        bin_name = "language_server.exe" if os.name == "nt" else "language_server"
        shutil.copyfile(os.path.join(res_path, "bin", bin_name), os.path.join(script_dir, "language_server.ru"))
    except Exception:
        pass

    ok("Локализация полностью завершена! Перезапустите Antigravity.")
    return True


def do_switch_language(target_lang, manager_path=None):
    res_path = get_resources_path(manager_path)
    if not res_path or not os.path.isdir(res_path):
        err("Каталог ресурсов Antigravity не найден.")
        return False

    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_name = "language_server.exe" if os.name == "nt" else "language_server"
    target_bin = os.path.join(res_path, "bin", bin_name)
    target_asar = os.path.join(res_path, "app.asar")

    if target_lang == "ru":
        info("Переключение на русский язык...")
        ru_asar = os.path.join(script_dir, "app.asar.ru")
        ru_bin = os.path.join(script_dir, "language_server.ru")
        if not os.path.exists(ru_asar) or not os.path.exists(ru_bin):
            info("Сборка свежего русского пакета...")
            return do_localize(manager_path)
        shutil.copyfile(ru_asar, target_asar)
        shutil.copyfile(ru_bin, target_bin)
        os.chmod(target_bin, 0o755)
        if sys.platform == "darwin":
            subprocess.run(["codesign", "--force", "--deep", "--sign", "-", target_bin], check=True)
        ok("Интерфейс успешно переключен на РУССКИЙ язык!")
        return True

    elif target_lang == "en":
        info("Переключение на оригинальный английский язык...")
        orig_asar = os.path.join(res_path, "app.asar.orig")
        orig_bin = os.path.join(res_path, "bin", bin_name + ".orig")
        if not os.path.exists(orig_asar) or not os.path.exists(orig_bin):
            err("Оригинальные резервные копии (.orig) не найдены!")
            return False
        shutil.copyfile(orig_asar, target_asar)
        shutil.copyfile(orig_bin, target_bin)
        os.chmod(target_bin, 0o755)
        if sys.platform == "darwin":
            subprocess.run(["codesign", "--force", "--deep", "--sign", "-", target_bin], check=True)
        ok("Интерфейс успешно переключен на АНГЛИЙСКИЙ язык!")
        return True


def do_install_rules():
    step("Установка глобальных русскоязычных правил и навыка i18n...")
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    user_home = os.path.expanduser("~")
    plugin_dir = os.path.join(user_home, ".gemini", "config", "plugins", "russian-dev-plugin")
    
    os.makedirs(os.path.join(plugin_dir, "rules"), exist_ok=True)
    os.makedirs(os.path.join(plugin_dir, "skills", "i18n-helper"), exist_ok=True)

    src_rules = os.path.join(script_dir, "rules", "russian-development.md")
    src_skill = os.path.join(script_dir, "skills", "i18n-helper", "SKILL.md")

    if os.path.exists(src_rules):
        shutil.copyfile(src_rules, os.path.join(plugin_dir, "rules", "russian-development.md"))
        shutil.copyfile(src_rules, os.path.join(script_dir, "GEMINI.md"))
    if os.path.exists(src_skill):
        shutil.copyfile(src_skill, os.path.join(plugin_dir, "skills", "i18n-helper", "SKILL.md"))

    plugin_json = os.path.join(plugin_dir, "plugin.json")
    with open(plugin_json, "w", encoding="utf-8") as f:
        f.write('{"name":"russian-dev-plugin","version":"1.0.0","description":"Русскоязычные правила разработки и инструмент автолокализации."}\n')

    ok("Глобальные правила и навык i18n-helper успешно установлены в ~/.gemini/config/plugins/!")
    return True
