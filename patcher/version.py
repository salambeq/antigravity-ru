# -*- coding: utf-8 -*-
"""
Централизованный модуль вычисления и отслеживания версии Antigravity Toolkit.
Автоматически учитывает любые изменения в кодовой базе:
  • При наличии Git: извлекает номер ревизии (число коммитов), хеш коммита и статус локальных правок (dirty).
  • При любых локальных правках (до коммита): формирует уникальный суффикс ревизии с хешем изменений.
  • При отсутствии Git (бандл): использует сохраненный штамп из version.json.
"""

import os
import sys
import json
import hashlib
import subprocess

BASE_VERSION = "2.0.7"
GITHUB_REPO = "salambeq/antigravity-ru"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPO}"

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_git_metadata(root_dir):
    """Извлекает динамическую информацию о ревизии Git."""
    try:
        rev = subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=root_dir,
            stderr=subprocess.DEVNULL,
            timeout=1.5,
        ).decode().strip()

        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root_dir,
            stderr=subprocess.DEVNULL,
            timeout=1.5,
        ).decode().strip()

        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=root_dir,
            stderr=subprocess.DEVNULL,
            timeout=1.5,
        ).decode().strip()

        is_dirty = bool(status)
        dirty_hash = ""
        if is_dirty:
            dirty_hash = hashlib.sha1(status.encode("utf-8")).hexdigest()[:6]

        return int(rev), commit, is_dirty, dirty_hash
    except Exception:
        return None, None, False, ""


def _load_version_stamp(root_dir):
    """Считывает зафиксированную версию из version.json при автономном запуске."""
    vfile = os.path.join(root_dir, "version.json")
    if os.path.isfile(vfile):
        try:
            with open(vfile, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def resolve_version_info(root_dir=None):
    """Вычисляет полную структуру данных о текущей версии с учетом правок."""
    if root_dir is None:
        root_dir = _ROOT_DIR

    stamp = _load_version_stamp(root_dir)
    base_ver = stamp.get("base_version") or BASE_VERSION

    rev, commit, is_dirty, dirty_hash = _get_git_metadata(root_dir)

    if rev is not None and commit is not None:
        if is_dirty:
            display_ver = f"{base_ver}.{rev}-dev+{commit}.{dirty_hash}"
            short_ver = f"{base_ver}-dev"
            label = f"v{base_ver} (rev {rev} · {commit}*)"
        else:
            display_ver = f"{base_ver}.{rev}"
            short_ver = base_ver
            label = f"v{base_ver} (rev {rev} · {commit})"
        return {
            "base_version": base_ver,
            "version": display_ver,
            "short_version": short_ver,
            "full_version": label,
            "build_rev": rev,
            "commit": commit,
            "is_dirty": is_dirty,
            "dirty_hash": dirty_hash,
            "github_repo": GITHUB_REPO,
            "github_url": GITHUB_REPO_URL,
        }

    # Фоллбэк, если репозиторий упакован без каталога .git
    saved_ver = stamp.get("version", base_ver)
    saved_rev = stamp.get("build_rev", 0)
    saved_commit = stamp.get("commit", "release")
    return {
        "base_version": base_ver,
        "version": saved_ver,
        "short_version": base_ver,
        "full_version": f"v{saved_ver} ({saved_commit})",
        "build_rev": saved_rev,
        "commit": saved_commit,
        "is_dirty": False,
        "dirty_hash": "",
        "github_repo": GITHUB_REPO,
        "github_url": GITHUB_REPO_URL,
    }


# Экспортируемые глобальные константы
_INFO = resolve_version_info()
VERSION = _INFO["version"]
VERSION_SHORT = _INFO["short_version"]
VERSION_FULL = _INFO["full_version"]
BUILD_REV = _INFO["build_rev"]
BUILD_COMMIT = _INFO["commit"]
IS_DIRTY = _INFO["is_dirty"]


def get_version():
    """Возвращает актуальную версию приложения."""
    return resolve_version_info()["version"]


def get_full_version_string():
    """Возвращает форматированную строку с ревизией и хешем."""
    return resolve_version_info()["full_version"]
