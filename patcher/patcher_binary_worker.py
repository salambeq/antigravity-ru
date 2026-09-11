import os
import sys
import io
import zipfile
import struct
import subprocess
import shutil

def patch_language_server(app_res, script_dir, preserve_or_apply_unlock=True):
    bin_name = "language_server.exe" if os.name == "nt" else "language_server"
    orig_bin = os.path.join(app_res, "bin", bin_name + ".orig")
    import tempfile
    target_bin = os.path.join(tempfile.gettempdir(), f"antigravity_ls_patched_{os.getpid()}" + (".exe" if os.name == "nt" else ""))
    bundle_dir = os.path.join(script_dir, "frontend_bundle")
    if not os.path.isdir(bundle_dir) and getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundle_dir = os.path.join(sys._MEIPASS, "frontend_bundle")

    if not os.path.exists(orig_bin):
        if os.path.exists(dest_bin):
            shutil.copyfile(dest_bin, orig_bin)
        else:
            raise FileNotFoundError(f"Neither {dest_bin} nor {orig_bin} found!")

    # Проверяем, был ли dest_bin уже разблокирован (региональный патч)
    was_unlocked = False
    try:
        from patcher.manager.patcher import is_already_patched
        was_unlocked = is_already_patched(dest_bin)
    except Exception:
        pass

    # 1. Перепаковка frontend_bundle в ZIP
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(bundle_dir):
            for file in sorted(files):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, bundle_dir)
                zf.write(full_path, rel_path)

    new_zip = zip_buf.getvalue()
    new_len = len(new_zip)

    # Читаем оригинальный бинарник
    with open(orig_bin, 'rb') as f:
        data = bytearray(f.read())

    # 2. Поиск EOCD ZIP в бинарнике
    eocd_pos = data.rfind(b'PK\x05\x06')
    if eocd_pos == -1:
        raise ValueError("Could not find ZIP EOCD signature in binary!")

    comment_len = int.from_bytes(data[eocd_pos+20:eocd_pos+22], 'little')
    cd_size = int.from_bytes(data[eocd_pos+12:eocd_pos+16], 'little')
    cd_offset = int.from_bytes(data[eocd_pos+16:eocd_pos+20], 'little')
    true_zip_start = eocd_pos - cd_size - cd_offset
    zip_end = eocd_pos + 22 + comment_len
    orig_len = zip_end - true_zip_start

    if new_len > orig_len:
        raise ValueError(f"New zip ({new_len}) is larger than original ({orig_len})!")

    # 3. Поиск структуры Go-слайса { ptr, len, cap }
    target_len_bytes = struct.pack('<Q', orig_len)
    slice_pos = -1
    for pos in range(0, len(data) - 24, 8):
        if data[pos+8:pos+16] == target_len_bytes and data[pos+16:pos+24] == target_len_bytes:
            ptr = struct.unpack('<Q', data[pos:pos+8])[0]
            if ptr & 0xFFFFFFFF == true_zip_start or (ptr >= true_zip_start and (ptr - true_zip_start) % 0x100000000 == 0):
                slice_pos = pos
                break

    if slice_pos == -1:
        for pos in range(0, len(data) - 16, 4):
            if data[pos:pos+4] == struct.pack('<I', true_zip_start):
                slice_pos = pos
                break

    # 4. Замена ZIP-архива в памяти
    data[true_zip_start : true_zip_start + new_len] = new_zip
    if new_len < orig_len:
        data[true_zip_start + new_len : true_zip_start + orig_len] = b'\x00' * (orig_len - new_len)

    # 5. Обновление длины слайса
    if slice_pos != -1:
        struct.pack_into('<Q', data, slice_pos + 8, new_len)
        struct.pack_into('<Q', data, slice_pos + 16, new_len)

    # 6. Если бинарник был разблокирован (или нужно применить unlock) — сохраняем/применяем разблокировку
    if preserve_or_apply_unlock and was_unlocked:
        try:
            from patcher.manager.patcher import MANAGER_GATE
            kind, off, matched_gate = MANAGER_GATE.resolve(data)
            if kind == "unpatched":
                data[off : off + len(matched_gate.fix)] = matched_gate.fix
        except Exception:
            pass

    # 7. Запись модифицированного файла
    with open(target_bin, 'wb') as f:
        f.write(data)
    os.chmod(target_bin, 0o755)

    if sys.platform == 'darwin':
        subprocess.run(['codesign', '--force', '--deep', '--sign', '-', target_bin], check=True)

    temp_dest = dest_bin + '.tmp'
    shutil.copyfile(target_bin, temp_dest)
    os.chmod(temp_dest, 0o755)
    if sys.platform == 'darwin':
        subprocess.run(['codesign', '--force', '--deep', '--sign', '-', temp_dest], check=True)
    os.replace(temp_dest, dest_bin)
