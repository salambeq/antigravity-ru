"""
Модуль управления мультиаккаунтом и автоматической ротации квот Antigravity.
"""

from patcher.accounts.keychain import (
    read_current_token_raw,
    write_token_raw,
    decode_token_payload,
    encode_token_payload,
)
from patcher.accounts.manager import AccountManager
from patcher.accounts.rotator import QuotaRotator

__all__ = [
    "read_current_token_raw",
    "write_token_raw",
    "decode_token_payload",
    "encode_token_payload",
    "AccountManager",
    "QuotaRotator",
]
