import os
import sys
import shutil
import subprocess
import tempfile
from patcher.utils.console import ok, info, warn, err, step

def patch_app_asar(app_res, script_dir):
    """
    Распаковывает app.asar, применяет перевод интерфейса и запаковывает обратно.
    Если npx недоступен, использует готовый предсобранный app.asar.ru.
    """
    orig_asar = os.path.join(app_res, "app.asar.orig")
    dest_asar = os.path.join(app_res, "app.asar")
    unpacked_dir = os.path.join(app_res, "app.asar.unpacked")
    ru_asar_cache = os.path.join(script_dir, "app.asar.ru")
    if not os.path.exists(ru_asar_cache) and getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        ru_asar_cache = os.path.join(sys._MEIPASS, "app.asar.ru")

    if not os.path.exists(orig_asar):
        if os.path.exists(dest_asar):
            shutil.copyfile(dest_asar, orig_asar)
            info(f"Создана резервная копия: {orig_asar}")
        else:
            raise FileNotFoundError(f"Файл {dest_asar} не найден!")

    # Проверяем наличие npx
    npx_bin = shutil.which("npx")
    if npx_bin:
        info("Распаковка и сборка локализованного app.asar через @electron/asar...")
        temp_dir = tempfile.mkdtemp(prefix="antigravity_asar_")
        try:
            temp_asar = os.path.join(temp_dir, "app.asar")
            shutil.copyfile(orig_asar, temp_asar)

            # Для корректной распаковки asar требуется наличие <name>.unpacked
            if os.path.exists(unpacked_dir):
                target_unpacked = os.path.join(temp_dir, "app.asar.unpacked")
                try:
                    os.symlink(unpacked_dir, target_unpacked)
                except (OSError, AttributeError):
                    try:
                        shutil.copytree(unpacked_dir, target_unpacked)
                    except Exception:
                        pass

            asar_extract_dir = os.path.join(temp_dir, "extracted")
            packed_asar = os.path.join(temp_dir, "packed.asar")

            # 1. Распаковка
            cmd_extract = [npx_bin, "--yes", "@electron/asar", "extract", temp_asar, asar_extract_dir]
            res_ext = subprocess.run(cmd_extract, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_ext.returncode != 0:
                raise RuntimeError(f"Ошибка распаковки asar: {res_ext.stderr}")

            # 2. Модификация файлов
            dist_dir = os.path.join(asar_extract_dir, "dist")
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                sys.path.insert(0, sys._MEIPASS)
            sys.path.insert(0, script_dir)
            import patch_asar
            patch_asar.patch_asar_dir(dist_dir)

            # 3. Запаковка с распаковкой chrome-devtools-mcp
            cmd_pack = [
                npx_bin, "--yes", "@electron/asar", "pack",
                asar_extract_dir,
                packed_asar,
                "--unpack", "**/node_modules/chrome-devtools-mcp/**"
            ]
            res_pack = subprocess.run(cmd_pack, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_pack.returncode != 0:
                raise RuntimeError(f"Ошибка запаковки asar: {res_pack.stderr}")

            # 4. Копирование в целевую директорию и в кэш
            temp_dest = dest_asar + ".tmp"
            shutil.copyfile(packed_asar, temp_dest)
            os.replace(temp_dest, dest_asar)
            try:
                shutil.copyfile(packed_asar, ru_asar_cache)
            except Exception:
                pass
            ok("Модифицированный app.asar успешно собран и установлен!")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    elif os.path.exists(ru_asar_cache):
        info("npx не найден, используется предсобранный готовый app.asar.ru...")
        temp_dest = dest_asar + ".tmp"
        shutil.copyfile(ru_asar_cache, temp_dest)
        os.replace(temp_dest, dest_asar)
        ok("Предсобранный app.asar.ru успешно установлен!")
    else:
        raise RuntimeError("Для сборки app.asar требуется Node.js / npx, либо наличие готового app.asar.ru.")
