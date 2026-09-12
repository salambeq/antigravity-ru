#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
     ANTIGRAVITY TOOLKIT — АВТОМАТИЧЕСКОЕ УПРАВЛЕНИЕ ВЕРСИЕЙ ПРОЕКТА
================================================================================
Скрипт для синхронизации и инкремента версии приложения при любых изменениях:
  • Обновляет version.json, package.json, gui/package.json, patcher/version.py и README.md
  • Позволяет инкрементировать patch / minor / major версии
  • Поддерживает установку Git-хука для автоматической фиксации версии при коммитах
"""

import os
import sys
import re
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_git_info():
    try:
        rev = subprocess.check_output(["git", "rev-list", "--count", "HEAD"], cwd=ROOT_DIR, stderr=subprocess.DEVNULL).decode().strip()
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT_DIR, stderr=subprocess.DEVNULL).decode().strip()
        return int(rev), commit
    except Exception:
        return 0, "release"


def sync_all(new_base_version=None):
    version_json_path = os.path.join(ROOT_DIR, "version.json")
    pkg_json_path = os.path.join(ROOT_DIR, "package.json")
    gui_pkg_json_path = os.path.join(ROOT_DIR, "gui", "package.json")
    version_py_path = os.path.join(ROOT_DIR, "patcher", "version.py")
    readme_path = os.path.join(ROOT_DIR, "README.md")

    cur_data = load_json(version_json_path) if os.path.isfile(version_json_path) else {}
    base_ver = new_base_version or cur_data.get("base_version") or "2.0.7"

    rev, commit = get_git_info()

    # 1. Обновляем version.json
    vdata = {
        "base_version": base_ver,
        "version": f"{base_ver}.{rev}" if rev else base_ver,
        "build_rev": rev,
        "commit": commit,
        "github_repo": "salambeq/antigravity-ru",
        "github_url": "https://github.com/salambeq/antigravity-ru",
    }
    save_json(version_json_path, vdata)
    print(f"✓ version.json -> v{vdata['version']} (commit: {commit})")

    # 2. Обновляем package.json
    if os.path.isfile(pkg_json_path):
        pkg = load_json(pkg_json_path)
        pkg["version"] = base_ver
        save_json(pkg_json_path, pkg)
        print(f"✓ package.json -> {base_ver}")

    # 3. Обновляем gui/package.json
    if os.path.isfile(gui_pkg_json_path):
        gpkg = load_json(gui_pkg_json_path)
        gpkg["version"] = base_ver
        save_json(gui_pkg_json_path, gpkg)
        print(f"✓ gui/package.json -> {base_ver}")

    # 4. Обновляем patcher/version.py
    if os.path.isfile(version_py_path):
        with open(version_py_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'BASE_VERSION\s*=\s*"[^"]+"', f'BASE_VERSION = "{base_ver}"', content)
        with open(version_py_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ patcher/version.py -> BASE_VERSION = \"{base_ver}\"")

    # 5. Обновляем заголовок README.md
    if os.path.isfile(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()
        readme = re.sub(
            r'# 🇷🇺 Antigravity Toolkit & Русская локализация \(v[^\)]+\)',
            f'# 🇷🇺 Antigravity Toolkit & Русская локализация (v{base_ver})',
            readme,
        )
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme)
        print(f"✓ README.md -> заголовок обновлен до v{base_ver}")


def bump(part="patch"):
    version_json_path = os.path.join(ROOT_DIR, "version.json")
    cur_data = load_json(version_json_path) if os.path.isfile(version_json_path) else {}
    base_ver = cur_data.get("base_version", "2.0.7")

    parts = [int(p) for p in re.findall(r"\d+", base_ver)]
    while len(parts) < 3:
        parts.append(0)

    major, minor, patch = parts[0], parts[1], parts[2]
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    new_ver = f"{major}.{minor}.{patch}"
    print(f"🚀 Повышение версии: {base_ver} -> {new_ver}")
    sync_all(new_ver)
    return new_ver


def install_git_hook():
    hooks_dir = os.path.join(ROOT_DIR, ".git", "hooks")
    if not os.path.isdir(hooks_dir):
        print("❌ Каталог .git/hooks не найден.")
        return

    post_commit_hook = os.path.join(hooks_dir, "post-commit")
    hook_script = """#!/usr/bin/env bash
# Автоматическая синхронизация штампа версии после коммита
python3 scripts/bump_version.py --sync > /dev/null 2>&1 || true
"""
    with open(post_commit_hook, "w", encoding="utf-8") as f:
        f.write(hook_script)
    os.chmod(post_commit_hook, 0o755)
    print("✅ Git-хук post-commit успешно установлен в .git/hooks/post-commit")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--install-hook":
            install_git_hook()
        elif arg == "--sync":
            sync_all()
        elif arg in ("patch", "minor", "major"):
            bump(arg)
        elif re.match(r"^\d+\.\d+\.\d+", arg):
            sync_all(arg)
        else:
            print("Использование: python3 scripts/bump_version.py [patch|minor|major|X.Y.Z|--sync|--install-hook]")
    else:
        sync_all()
