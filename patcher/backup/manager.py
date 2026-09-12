#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль резервного копирования и восстановления пользовательских данных Antigravity.
Обеспечивает сохранность истории диалогов (conversations), артефактов (brain),
настроек сессий (app_storage.json) и токенов аккаунтов.
"""

from __future__ import annotations

import os
import sys
import time
import json
import tarfile
import shutil
import io
from typing import Optional, List, Dict, Tuple

from patcher.utils.console import (
    info,
    ok,
    warn,
    err,
    step,
    color,
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_BOLD,
)

DEFAULT_BACKUP_DIR = os.path.expanduser("~/.gemini/backups")


def format_bytes(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


class BackupManager:
    def __init__(self, backup_dir: str = DEFAULT_BACKUP_DIR):
        self.backup_dir = backup_dir
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, mode=0o700, exist_ok=True)
        try:
            os.chmod(self.backup_dir, 0o700)
        except OSError:
            pass

    @staticmethod
    def get_data_paths() -> dict:
        home = os.path.expanduser("~")
        gemini_dir = os.path.join(home, ".gemini")
        antigravity_dir = os.path.join(gemini_dir, "antigravity")

        conversations_dir = os.path.join(antigravity_dir, "conversations")
        brain_dir = os.path.join(antigravity_dir, "brain")
        state_file = os.path.join(antigravity_dir, "antigravity_state.pbtxt")
        proto_file = os.path.join(antigravity_dir, "agyhub_summaries_proto.pb")
        accounts_dir = os.path.join(gemini_dir, "accounts")

        # Application support storage (app_storage.json)
        storage_file = ""
        if sys.platform == "darwin":
            storage_file = os.path.join(home, "Library", "Application Support", "Antigravity", "app_storage.json")
        elif os.name == "nt":
            appdata = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
            storage_file = os.path.join(appdata, "Antigravity", "app_storage.json")
        else:
            # Linux
            cfg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
            storage_file = os.path.join(cfg, "Antigravity", "app_storage.json")

        return {
            "antigravity_dir": antigravity_dir,
            "conversations_dir": conversations_dir,
            "brain_dir": brain_dir,
            "state_file": state_file,
            "proto_file": proto_file,
            "storage_file": storage_file,
            "accounts_dir": accounts_dir,
        }

    def get_conversation_count(self) -> int:
        paths = self.get_data_paths()
        conv_dir = paths["conversations_dir"]
        if os.path.isdir(conv_dir):
            try:
                return len([f for f in os.listdir(conv_dir) if f.endswith(".db")])
            except Exception:
                pass
        return 0

    def create_backup(
        self,
        backup_type: str = "chats",
        dest_dir: Optional[str] = None,
        note: str = ""
    ) -> Tuple[bool, str, dict]:
        """
        Создает сжатый архив резервной копии данных Antigravity.
        backup_type: 'chats' (диалоги + настройки + аккаунты) или 'full' (+ brain артефакты)
        """
        target_dir = dest_dir or self.backup_dir
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, mode=0o700, exist_ok=True)

        paths = self.get_data_paths()
        conv_dir = paths["conversations_dir"]

        if not os.path.isdir(conv_dir) or not os.listdir(conv_dir):
            warn("Каталог диалогов пуст или не найден.")

        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        archive_name = f"antigravity_backup_{backup_type}_{timestamp_str}.tar.gz"
        archive_path = os.path.join(target_dir, archive_name)
        meta_path = os.path.join(target_dir, f"antigravity_backup_{backup_type}_{timestamp_str}.meta.json")

        chat_count = self.get_conversation_count()
        file_entries = []

        manifest = {
            "version": "1.0",
            "created_at": int(time.time()),
            "created_at_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
            "backup_type": backup_type,
            "platform": sys.platform,
            "chat_count": chat_count,
            "note": note or "Резервная копия чатов Antigravity",
            "files": [],
        }

        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                # 1. Сначала добавляем manifest.json в САМОЕ НАЧАЛО архива для быстрого чтения!
                manifest_placeholder = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
                ti = tarfile.TarInfo(name="manifest.json")
                ti.size = len(manifest_placeholder)
                ti.mtime = int(time.time())
                tar.addfile(ti, io.BytesIO(manifest_placeholder))

                # 2. Добавляем диалоги (conversations)
                if os.path.isdir(conv_dir):
                    info(f"Архивация диалогов ({chat_count} шт.)...")
                    for fname in os.listdir(conv_dir):
                        if fname.endswith((".db", ".db-wal", ".db-shm")):
                            fpath = os.path.join(conv_dir, fname)
                            if os.path.isfile(fpath):
                                arcname = os.path.join("conversations", fname)
                                tar.add(fpath, arcname=arcname)
                                file_entries.append(arcname)

                # 3. Добавляем сессионные файлы состояния
                if os.path.isfile(paths["state_file"]):
                    arcname = "antigravity_state.pbtxt"
                    tar.add(paths["state_file"], arcname=arcname)
                    file_entries.append(arcname)

                if os.path.isfile(paths["proto_file"]):
                    arcname = "agyhub_summaries_proto.pb"
                    tar.add(paths["proto_file"], arcname=arcname)
                    file_entries.append(arcname)

                # 4. Добавляем app_storage.json
                if paths["storage_file"] and os.path.isfile(paths["storage_file"]):
                    arcname = "app_storage.json"
                    tar.add(paths["storage_file"], arcname=arcname)
                    file_entries.append(arcname)

                # 5. Добавляем профили аккаунтов (accounts)
                acc_dir = paths["accounts_dir"]
                if os.path.isdir(acc_dir):
                    info("Архивация профилей аккаунтов...")
                    for root, _, files in os.walk(acc_dir):
                        for f in files:
                            fp = os.path.join(root, f)
                            rel = os.path.relpath(fp, acc_dir)
                            arcname = os.path.join("accounts", rel)
                            tar.add(fp, arcname=arcname)
                            file_entries.append(arcname)

                # 6. Если выбран full — добавляем brain (артефакты)
                if backup_type == "full" and os.path.isdir(paths["brain_dir"]):
                    info("Архивация артефактов и логов мозга (brain)...")
                    for root, _, files in os.walk(paths["brain_dir"]):
                        for f in files:
                            fp = os.path.join(root, f)
                            rel = os.path.relpath(fp, paths["brain_dir"])
                            arcname = os.path.join("brain", rel)
                            tar.add(fp, arcname=arcname)
                            file_entries.append(arcname)

            total_size = os.path.getsize(archive_path)
            manifest["total_size_bytes"] = total_size
            manifest["total_size_formatted"] = format_bytes(total_size)
            manifest["archive_path"] = archive_path
            manifest["archive_name"] = archive_name
            manifest["files"] = file_entries

            # Сохраняем sidecar .meta.json для мгновенного чтения без распаковки tar
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            try:
                os.chmod(meta_path, 0o600)
            except OSError:
                pass

            msg = (
                f"Резервная копия успешно создана!\n"
                f"  Файл:     {archive_name}\n"
                f"  Диалогов: {chat_count}\n"
                f"  Размер:   {format_bytes(total_size)}\n"
                f"  Каталог:  {target_dir}"
            )
            ok(msg)
            return True, msg, manifest

        except Exception as e:
            if os.path.exists(archive_path):
                try:
                    os.remove(archive_path)
                except OSError:
                    pass
            if os.path.exists(meta_path):
                try:
                    os.remove(meta_path)
                except OSError:
                    pass
            err_msg = f"Ошибка при создании резервной копии: {e}"
            err(err_msg)
            return False, err_msg, {}

    def list_backups(self) -> List[dict]:
        """
        Мгновенно возвращает список всех найденных резервных копий с метаданными.
        """
        results = []
        if not os.path.exists(self.backup_dir):
            return results

        for fname in sorted(os.listdir(self.backup_dir), reverse=True):
            if fname.startswith("antigravity_backup_") and fname.endswith((".tar.gz", ".tgz")):
                fpath = os.path.join(self.backup_dir, fname)
                base_stem = fname[:-7] if fname.endswith(".tar.gz") else fname[:-4]
                meta_path = os.path.join(self.backup_dir, f"{base_stem}.meta.json")

                try:
                    stat = os.stat(fpath)
                    entry = {
                        "filename": fname,
                        "path": fpath,
                        "size_bytes": stat.st_size,
                        "size_formatted": format_bytes(stat.st_size),
                        "created_at": int(stat.st_mtime),
                        "created_at_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                        "chat_count": 0,
                        "backup_type": "chats",
                        "note": "",
                    }

                    # 1. Сначала быстро читаем sidecar .meta.json (0 мс)
                    if os.path.isfile(meta_path):
                        try:
                            with open(meta_path, "r", encoding="utf-8") as f:
                                meta_data = json.load(f)
                            entry["chat_count"] = meta_data.get("chat_count", 0)
                            entry["backup_type"] = meta_data.get("backup_type", "chats")
                            entry["note"] = meta_data.get("note", "")
                            results.append(entry)
                            continue
                        except Exception:
                            pass

                    # 2. Иначе быстро читаем manifest.json из первого блока архива
                    try:
                        with tarfile.open(fpath, "r:gz") as tar:
                            first = tar.next()
                            if first and first.name == "manifest.json":
                                m_file = tar.extractfile(first)
                                if m_file:
                                    m_data = json.loads(m_file.read().decode("utf-8"))
                                    entry["chat_count"] = m_data.get("chat_count", 0)
                                    entry["backup_type"] = m_data.get("backup_type", "chats")
                                    entry["note"] = m_data.get("note", "")
                    except Exception:
                        pass

                    results.append(entry)
                except Exception:
                    pass

        return results

    def restore_backup(self, archive_path_or_filename: str) -> Tuple[bool, str]:
        """
        Восстанавливает диалоги и настройки из указанного файла резервной копии.
        """
        if not os.path.isabs(archive_path_or_filename):
            target_path = os.path.join(self.backup_dir, archive_path_or_filename)
        else:
            target_path = archive_path_or_filename

        if not os.path.isfile(target_path):
            return False, f"Файл резервной копии не найден: {target_path}"

        paths = self.get_data_paths()
        restored_chats = 0

        step(f"Восстановление данных из резервной копии {os.path.basename(target_path)}...")

        try:
            with tarfile.open(target_path, "r:gz") as tar:
                # Восстанавливаем файлы
                for member in tar.getmembers():
                    if member.name == "manifest.json":
                        continue

                    # 1. Диалоги
                    if member.name.startswith("conversations/"):
                        rel_name = member.name[len("conversations/"):]
                        if not rel_name:
                            continue
                        dest_conv = os.path.join(paths["conversations_dir"], rel_name)
                        os.makedirs(os.path.dirname(dest_conv), exist_ok=True)
                        f_in = tar.extractfile(member)
                        if f_in:
                            with open(dest_conv, "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)
                            if rel_name.endswith(".db"):
                                restored_chats += 1

                    # 2. Сессионные файлы состояния
                    elif member.name == "antigravity_state.pbtxt":
                        os.makedirs(paths["antigravity_dir"], exist_ok=True)
                        f_in = tar.extractfile(member)
                        if f_in:
                            with open(paths["state_file"], "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)

                    elif member.name == "agyhub_summaries_proto.pb":
                        os.makedirs(paths["antigravity_dir"], exist_ok=True)
                        f_in = tar.extractfile(member)
                        if f_in:
                            with open(paths["proto_file"], "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)

                    # 3. app_storage.json
                    elif member.name == "app_storage.json" and paths["storage_file"]:
                        os.makedirs(os.path.dirname(paths["storage_file"]), exist_ok=True)
                        f_in = tar.extractfile(member)
                        if f_in:
                            with open(paths["storage_file"], "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)

                    # 4. Профили аккаунтов
                    elif member.name.startswith("accounts/"):
                        rel_name = member.name[len("accounts/"):]
                        if not rel_name:
                            continue
                        dest_acc = os.path.join(paths["accounts_dir"], rel_name)
                        os.makedirs(os.path.dirname(dest_acc), exist_ok=True)
                        f_in = tar.extractfile(member)
                        if f_in:
                            with open(dest_acc, "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)

                    # 5. Brain (если был в архиве)
                    elif member.name.startswith("brain/"):
                        rel_name = member.name[len("brain/"):]
                        if not rel_name:
                            continue
                        dest_brain = os.path.join(paths["brain_dir"], rel_name)
                        os.makedirs(os.path.dirname(dest_brain), exist_ok=True)
                        f_in = tar.extractfile(member)
                        if f_in:
                            with open(dest_brain, "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)

            chat_msg = f"{restored_chats} диалогов" if restored_chats else "данные"
            success_msg = f"Успешно восстановлено {chat_msg} и настройки Antigravity! Перезапустите приложение, чтобы увидеть восстановленные чаты."
            ok(success_msg)
            return True, success_msg

        except Exception as e:
            err_msg = f"Ошибка при распаковке резервной копии: {e}"
            err(err_msg)
            return False, err_msg

    def delete_backup(self, archive_path_or_filename: str) -> Tuple[bool, str]:
        if not os.path.isabs(archive_path_or_filename):
            target_path = os.path.join(self.backup_dir, archive_path_or_filename)
        else:
            target_path = archive_path_or_filename

        base_stem = target_path[:-7] if target_path.endswith(".tar.gz") else target_path[:-4]
        meta_path = f"{base_stem}.meta.json"

        if not os.path.isfile(target_path):
            return False, "Файл резервной копии не существует."

        try:
            os.remove(target_path)
            if os.path.isfile(meta_path):
                os.remove(meta_path)
            return True, f"Резервная копия {os.path.basename(target_path)} удалена."
        except Exception as e:
            return False, f"Не удалось удалить файл: {e}"
