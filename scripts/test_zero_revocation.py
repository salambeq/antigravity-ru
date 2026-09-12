#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование механизма Zero-Revocation и мастера аккаунтов.
"""

import os
import sys
import json
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from patcher.accounts.keychain import (
    read_current_token_raw,
    write_token_raw,
    delete_current_token_raw,
    decode_token_payload,
    encode_token_payload,
)
from patcher.accounts.manager import AccountManager


def test_token_encode_decode():
    print("1. Тест кодирования/декодирования токена...", end=" ")
    sample = {
        "token": {
            "access_token": "mock_access_token_123",
            "refresh_token": "mock_refresh_token_456",
            "expiry": "2026-09-12T20:00:00Z"
        },
        "auth_method": "consumer"
    }
    encoded = encode_token_payload(sample)
    assert encoded.startswith("go-keyring-base64:"), "Префикс должен быть go-keyring-base64:"
    decoded = decode_token_payload(encoded)
    assert decoded["token"]["access_token"] == "mock_access_token_123"
    assert decoded["token"]["refresh_token"] == "mock_refresh_token_456"
    print("✅ OK")


def test_metadata_dual_sync():
    print("2. Тест синхронизации metadata.json и accounts_meta.json...", end=" ")
    mgr = AccountManager()
    meta = mgr._load_metadata()
    mgr._save_metadata(meta)

    # Проверяем наличие обоих файлов
    assert os.path.isfile(mgr.meta_path), "metadata.json должен существовать"
    assert os.path.isfile(mgr.alt_meta_path), "accounts_meta.json должен существовать"

    with open(mgr.meta_path, "r", encoding="utf-8") as f1, open(mgr.alt_meta_path, "r", encoding="utf-8") as f2:
        d1 = json.load(f1)
        d2 = json.load(f2)
        assert d1 == d2, "metadata.json и accounts_meta.json должны быть полностью идентичны"
    print("✅ OK")


def test_antigravity_accounts_compatibility():
    print("3. Тест каталога совместимости ~/.gemini/antigravity_accounts...", end=" ")
    alt_dir = os.path.expanduser("~/.gemini/antigravity_accounts")
    assert os.path.exists(alt_dir), "~/.gemini/antigravity_accounts должен существовать"
    
    # Проверяем доступность слотов через этот каталог
    mgr = AccountManager()
    slots = mgr.list_slots(auto_heal=False)
    for s_num in slots:
        slot_alt_path = os.path.join(alt_dir, f"slot_{s_num}.json")
        assert os.path.isfile(slot_alt_path), f"Файл {slot_alt_path} должен существовать"
    print("✅ OK")


def test_wizard_snapshot_and_rollback():
    print("4. Тест создания снимка сессии и отката (Zero-Loss Rollback)...", end=" ")
    mgr = AccountManager()
    
    # Считываем реальный токен перед тестом
    original_raw = read_current_token_raw()
    assert original_raw, "В Keychain должен присутствовать активный токен для теста"
    
    # Имитируем состояние мастера для тестового слота 99 (без перезапуска процессов)
    wizard_state = {
        "target_slot": 99,
        "previous_active_slot": mgr._load_metadata().get("active_slot"),
        "previous_token_raw": original_raw,
        "started_at": int(time.time()),
    }
    with open(mgr.wizard_path, "w", encoding="utf-8") as f:
        json.dump(wizard_state, f)

    # Проверяем отмену мастера
    # Подменяем pkill/open во время теста, чтобы не перезапускать Antigravity
    import subprocess
    orig_run = subprocess.run
    def mock_run(cmd, *args, **kwargs):
        if any(x in cmd for x in ["pkill", "open", "taskkill"]):
            class MockRes:
                returncode = 0
                stdout = ""
                stderr = ""
            return MockRes()
        return orig_run(cmd, *args, **kwargs)

    subprocess.run = mock_run
    try:
        ok_cancel, cancel_msg = mgr.cancel_wizard()
        assert ok_cancel, f"Откат мастера должен быть успешным: {cancel_msg}"
        assert not os.path.exists(mgr.wizard_path), "pending_wizard.json должен быть удален"
        
        # Проверяем, что исходный токен на месте
        restored_raw = read_current_token_raw()
        assert restored_raw == original_raw, "Токен в Keychain должен быть восстановлен в точности"
    finally:
        subprocess.run = orig_run

    print("✅ OK")


def main():
    print("\n--- Запуск тестов модуля Zero-Revocation ---")
    test_token_encode_decode()
    test_metadata_dual_sync()
    test_antigravity_accounts_compatibility()
    test_wizard_snapshot_and_rollback()
    print("\n🎉 Все тесты успешно пройдены!\n")


if __name__ == "__main__":
    main()
