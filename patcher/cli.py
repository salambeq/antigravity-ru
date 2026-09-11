import os
import sys
import webbrowser
import locale

from patcher.constants import (
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_BOLD,
    COLOR_DIM,
    COLOR_WHITE,
    COLOR_UNDERLINE,
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
)

def pause(prompt="  Нажмите Enter для продолжения..."):
    print(color(prompt, COLOR_DIM), end="", flush=True)
    if os.name == "nt":
        import msvcrt
        try:
            while msvcrt.kbhit():
                msvcrt.getch()
            while True:
                ch = msvcrt.getch()
                if ch in (b"\r", b"\n"):
                    break
        except Exception:
            input()
    else:
        try:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
                    if ch in ("\r", "\n"):
                        break
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            input()
    print()


def print_launch_examples():
    script_name = os.path.basename(sys.argv[0]) or "main.py"
    cmd = script_name if getattr(sys, "frozen", False) else f"python3 {script_name}"
    windows_example = f'{cmd} "C:\\Path\\To\\Antigravity IDE"'
    macos_example = f'{cmd} "/Applications/Antigravity IDE.app"'
    linux_example = f'{cmd} "/usr/share/antigravity-ide"'

    hint("Примеры запуска с указанием пути:")
    print(f"      Windows: {color(windows_example, COLOR_YELLOW)}")
    print(f"      macOS:   {color(macos_example, COLOR_YELLOW)}")
    print(f"      Linux:   {color(linux_example, COLOR_YELLOW)}")


def print_path_examples():
    windows_path = r"C:\Users\Name\AppData\Local\Programs\Antigravity IDE"
    macos_path = "/Applications/Antigravity IDE.app"
    linux_path = "/usr/share/antigravity-ide"

    hint("Примеры путей:")
    print(f"      Windows: {color(windows_path, COLOR_YELLOW)}")
    print(f"      macOS:   {color(macos_path, COLOR_YELLOW)}")
    print(f"      Linux:   {color(linux_path, COLOR_YELLOW)}")


def _read_console_line(prompt):
    print(prompt, end="", flush=True)

    stdin_buffer = getattr(sys.stdin, "buffer", None)
    if stdin_buffer is None:
        return sys.stdin.readline().rstrip("\r\n")

    raw = stdin_buffer.readline()
    if not raw:
        return ""

    encodings = [
        sys.stdin.encoding,
        locale.getpreferredencoding(False),
        "utf-8",
        "cp1251",
        "latin-1",
    ]
    for encoding in [e for e in encodings if e]:
        try:
            return raw.decode(encoding).rstrip("\r\n")
        except UnicodeDecodeError:
            pass

    return raw.decode("utf-8", errors="replace").rstrip("\r\n")


def prompt_yn(question):
    question = question.rstrip()
    prompt = f"  [?] {question} ({color('y', COLOR_GREEN)}/{color('n', COLOR_RED)}): "
    return _read_console_line(prompt).strip().lower()


def confirmed(question):
    """Возвращает True, если пользователь подтвердил действие ('y', 'д', 'да', 'yes')."""
    return prompt_yn(question) in ("y", "yes", "д", "да")


def offer_download_and_block(software_name="Antigravity", target_type=None):
    err(f"Путь к {software_name} не задан или программа не установлена.")
    err("Операция отменена.")
    hint(f"Страница загрузки: {color(DOWNLOAD_URL, COLOR_CYAN)}")
    print()
    print_menu_row("1", "Открыть страницу загрузки в браузере", DOWNLOAD_URL, COLOR_GREEN)
    print_menu_row("2", f"Указать путь к {software_name} вручную", "ручной выбор пути", COLOR_CYAN)
    print_menu_row("0", "Вернуться назад", "", COLOR_RED)
    print()

    action = input(color("  Выберите действие > ", COLOR_CYAN, COLOR_BOLD)).strip()
    if action == "1":
        webbrowser.open(DOWNLOAD_URL)
        ok(f"Открываем: {color(DOWNLOAD_URL, COLOR_CYAN)}")
        return None
    elif action == "2":
        from patcher.ide.discovery import resolve_target_path, find_main_js
        from patcher.manager.discovery import resolve_manager_path
        from patcher.agy.discovery import resolve_agy_path

        print()
        hint(f"Введите путь к {software_name}:")
        print_path_examples()
        raw = input(color(f"\n  Путь к {software_name} > ", COLOR_CYAN, COLOR_BOLD)).strip()
        if raw:
            if target_type == "ide" or software_name == "Antigravity IDE":
                new_path = resolve_target_path(raw)
                if new_path and os.path.isdir(new_path):
                    new_path = find_main_js(new_path)
                if new_path and os.path.isfile(new_path) and new_path.endswith("main.js"):
                    ok(f"Путь к {software_name} обновлен!")
                    return new_path
                else:
                    err(f"Не удалось найти main.js для {software_name}.")
            elif target_type == "manager" or software_name == "Antigravity 2.0":
                new_path = resolve_manager_path(raw)
                if new_path and os.path.isfile(new_path):
                    ok(f"Путь к {software_name} обновлен!")
                    return new_path
                else:
                    err(f"Не удалось найти language_server для {software_name}.")
            elif target_type == "agy" or software_name == "Antigravity CLI":
                new_path = resolve_agy_path(raw)
                if new_path and os.path.isfile(new_path):
                    ok(f"Путь к {software_name} обновлен!")
                    return new_path
    else:
        cancel("Отменено.")
        return None
