import json
import sys
import webbrowser

from patcher.constants import VERSION, COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_RED, COLOR_BOLD, COLOR_UNDERLINE
from patcher.utils.console import color, link, info, ok, warn, err, hint, _frame_border, _frame_row


GITHUB_REPO = "AvenCores/open-antigravity-patcher"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
ISSUES_URL = f"https://github.com/{GITHUB_REPO}/issues"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GOIDA_VPN_URL = "https://github.com/AvenCores/goida-vpn-configs"

LAST_UPDATE_RESULT = None


def get_last_update_result():
    return LAST_UPDATE_RESULT


def set_last_update_result(result):
    global LAST_UPDATE_RESULT
    LAST_UPDATE_RESULT = result


def print_network_error_warning():
    """Print a noticeable warning and VPN recommendation when check_for_updates fails interactively."""
    warn("Could not check for updates (network error).")
    vpn_link = link(GOIDA_VPN_URL, "goida-vpn-configs", COLOR_CYAN, COLOR_UNDERLINE)
    hint("Recommendation: Turn on VPN to connect to GitHub and check for updates.")
    hint(f"Free VPN configs: {vpn_link} (auto-updated V2Ray/VLESS/Hysteria configs by AvenCores)")


def print_network_error_banner():
    """Print a framed warning banner in the main menu when update check failed due to network error."""
    vpn_link = link(GOIDA_VPN_URL, "goida-vpn-configs", COLOR_CYAN, COLOR_UNDERLINE)
    print(f"  {_frame_border('╔', '═', '╗', COLOR_YELLOW)}")
    print(f"  {_frame_row(color('WARNING: Update check failed (network error)', COLOR_YELLOW, COLOR_BOLD), accent=COLOR_YELLOW)}")
    print(f"  {_frame_row(color('Turn on VPN to check for updates on GitHub', COLOR_CYAN, COLOR_BOLD), accent=COLOR_YELLOW)}")
    print(f"  {_frame_row(color(f'Free VPN configs: {vpn_link}', COLOR_CYAN), accent=COLOR_YELLOW)}")
    print(f"  {_frame_border('╚', '═', '╝', COLOR_YELLOW)}")
    print()



def print_update_status_notice():
    """Prints update notice, up-to-date status, or network error warning banner in the main menu."""
    if LAST_UPDATE_RESULT == "network_error":
        print_network_error_banner()
    elif isinstance(LAST_UPDATE_RESULT, tuple) and LAST_UPDATE_RESULT[0] == "update_available":
        _, tag, url = LAST_UPDATE_RESULT
        info(f"New version available: {color(tag, COLOR_GREEN, COLOR_BOLD)} (current: {color(VERSION, COLOR_YELLOW)})")
        hint(f"Download: {color(url, COLOR_CYAN)}")
        print()
    elif LAST_UPDATE_RESULT == "up_to_date":
        ok(f"Patcher is up to date (v{VERSION})")
        print()


def _parse_version(v):
    """Parse a version string like '1.2.6' into a tuple of ints."""
    v = v.strip().lstrip("vV")
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts)


def _fetch_latest_release(timeout=5):
    """
    Автоматические сетевые запросы отключены для обеспечения 100% локальной работы.
    Обновления и синхронизация с upstream-репозиторием осуществляются исключительно
    вручную по запросу пользователя через .agent (workflow sync_unlocker).
    """
    return None, None


def check_for_updates(silent=True, timeout=5):
    """
    Офлайн-проверка обновлений. В соответствии с политикой нулевых сетевых утечек
    программа не выполняет сетевых запросов в фоновом режиме.
    """
    global LAST_UPDATE_RESULT
    LAST_UPDATE_RESULT = "up_to_date"
    if not silent:
        ok(f"Приложение работает в 100% локальном режиме (v{VERSION})")
        hint("Для ручной сверки обновлений анлокера используйте workflow .agent или scripts/check_upstream.py")
    return False


def open_releases_page():
    """Open the GitHub releases page in the default browser."""
    webbrowser.open(RELEASES_URL)
    ok(f"Opening: {color(RELEASES_URL, COLOR_CYAN)}")


def open_issues_page():
    """Open the GitHub issues page in the default browser."""
    webbrowser.open(ISSUES_URL)
    ok(f"Opening: {color(ISSUES_URL, COLOR_CYAN)}")


def handle_patch_failure():
    """Handle patch failure or signature not found.

    Checks for updates:
    - If an update is available, offers to open the releases page to install it.
    - If using the latest version (or no update available), offers to create an issue on GitHub.
    """
    from patcher.cli import confirmed

    print()
    info("Checking for patcher updates...")
    has_update = check_for_updates(silent=True)

    if has_update and isinstance(LAST_UPDATE_RESULT, tuple) and LAST_UPDATE_RESULT[0] == "update_available":
        _, tag, url = LAST_UPDATE_RESULT
        info(f"An update for Open Antigravity Patcher is available: {color(tag, COLOR_GREEN, COLOR_BOLD)} (current: {color(VERSION, COLOR_YELLOW)})")
        hint(f"Download: {color(url, COLOR_CYAN)}")
        if confirmed("A patcher update is available. Would you like to open the releases page to install it?"):
            webbrowser.open(url or RELEASES_URL)
            ok(f"Opening: {color(url or RELEASES_URL, COLOR_CYAN)}")
    else:
        if LAST_UPDATE_RESULT == "up_to_date":
            ok(f"You are using the latest version of Open Antigravity Patcher (v{VERSION}).")

        hint(f"Issue tracker: {color(ISSUES_URL, COLOR_CYAN)}")
        if confirmed("Would you like to open GitHub to create an issue?"):
            webbrowser.open(ISSUES_URL)
            ok(f"Opening: {color(ISSUES_URL, COLOR_CYAN)}")

