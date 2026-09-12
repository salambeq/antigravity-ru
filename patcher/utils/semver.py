# -*- coding: utf-8 -*-
"""
================================================================================
          ANTIGRAVITY TOOLKIT — МОДУЛЬ СРАВНЕНИЯ СЕМАНТИЧЕСКИХ ВЕРСИЙ
================================================================================
Предоставляет класс Version для парсинга и сравнения семантических версий
(SemVer) без обязательной зависимости от сторонней библиотеки packaging.

При наличии packaging используется нативный packaging.version.Version.
При отсутствии packaging активируется встроенный парсер на чистом Python,
полностью совместимый по операциям сравнения (==, !=, <, <=, >, >=).
================================================================================
"""

import re
from typing import Any, Tuple, Optional

try:
    from packaging.version import Version as _PkgVersion  # type: ignore
except ImportError:
    _PkgVersion = None


class _PureVersion:
    """
    Встроенная легковесная реализация SemVer на чистом Python.
    Поддерживает версии вида '2.9.1', 'v2.9.1', '1.107.0', '2.0.7-alpha', '2.0.7.1'.
    """

    def __init__(self, version_str: Any) -> None:
        if isinstance(version_str, (_PureVersion,)):
            self.raw: str = version_str.raw
            self.parts: Tuple[int, ...] = version_str.parts
            self.pre: Tuple[int, int] = version_str.pre
            return
        if _PkgVersion is not None and isinstance(version_str, _PkgVersion):
            version_str = str(version_str)

        if not isinstance(version_str, str):
            version_str = str(version_str)

        self.raw = version_str.strip()
        v = self.raw.lstrip("vV").strip()
        if not v:
            raise ValueError(f"Недопустимая строка версии: '{version_str}'")

        # Извлекаем числовую часть версий (например '2.9.1')
        m = re.match(r"^(\d+(?:\.\d+)*)", v)
        if not m:
            raise ValueError(f"Недопустимый формат версии: '{version_str}'")

        self.parts = tuple(int(x) for x in m.group(1).split("."))

        # Обработка суффиксов (alpha, beta, rc, dev, preview и др.)
        rest = v[m.end():].strip("-.")
        if rest:
            pre_m = re.match(r"^(a|b|rc|alpha|beta|dev|preview|insider)(\d*)", rest, re.I)
            if pre_m:
                tag, num = pre_m.groups()
                tag_map = {
                    "dev": 0,
                    "a": 1,
                    "alpha": 1,
                    "b": 2,
                    "beta": 2,
                    "rc": 3,
                    "preview": 3,
                    "insider": 4,
                }
                self.pre = (tag_map.get(tag.lower(), 1), int(num) if num else 0)
            else:
                self.pre = (0, 0)
        else:
            # Полноценный релиз всегда старше любого пререлиза
            self.pre = (999, 0)

    @property
    def _cmp_key(self) -> Tuple[Tuple[int, ...], Tuple[int, int]]:
        # Дополняем кортеж до 4 чисел для консистентного сравнения
        parts_padded = self.parts + (0,) * max(0, 4 - len(self.parts))
        return (parts_padded, self.pre)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, _PureVersion):
            try:
                other = _PureVersion(str(other))
            except Exception:
                return NotImplemented
        return self._cmp_key == other._cmp_key

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, _PureVersion):
            try:
                other = _PureVersion(str(other))
            except Exception:
                return NotImplemented
        return self._cmp_key < other._cmp_key

    def __le__(self, other: Any) -> bool:
        return self < other or self == other

    def __gt__(self, other: Any) -> bool:
        return not (self <= other)

    def __ge__(self, other: Any) -> bool:
        return not (self < other)

    def __str__(self) -> str:
        return self.raw

    def __repr__(self) -> str:
        return f"<Version '{self.raw}'>"


if _PkgVersion is not None:
    class Version(_PkgVersion):  # type: ignore
        """Обёртка над packaging.version.Version с безопасной инициализацией."""
        def __init__(self, version_str: Any) -> None:
            if isinstance(version_str, str):
                cleaned = version_str.strip().lstrip("vV")
            else:
                cleaned = str(version_str).strip().lstrip("vV")
            super().__init__(cleaned)
else:
    Version = _PureVersion  # type: ignore


def parse_version_safe(ver_str: Optional[str]) -> Optional[Version]:
    """
    Безопасно парсит строку версии в объект Version.
    Возвращает None, если строка пустая или имеет неверный формат.
    """
    if not ver_str:
        return None
    try:
        return Version(ver_str)
    except Exception:
        return None
