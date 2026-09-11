import os, sys, io, zipfile, struct, subprocess, shutil, time, signal

def find_app_resources():
    env_path = os.environ.get("ANTIGRAVITY_RESOURCES_PATH")
    if env_path and os.path.isdir(env_path):
        return env_path

    if sys.platform == 'darwin':
        paths = ["/Applications/Antigravity.app/Contents/Resources"]
    elif sys.platform.startswith('linux'):
        paths = [
            "/opt/Antigravity/resources",
            "/usr/lib/antigravity/resources",
            os.path.expanduser("~/.local/share/antigravity/resources")
        ]
    elif sys.platform == 'win32':
        local_app = os.environ.get("LOCALAPPDATA", "")
        prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        paths = [
            os.path.join(local_app, "Programs", "Antigravity", "resources"),
            os.path.join(prog_files, "Antigravity", "resources")
        ]
    else:
        paths = []

    for p in paths:
        if os.path.isdir(p):
            return p
    return paths[0] if paths else None

def get_binary_name():
    return "language_server.exe" if sys.platform == 'win32' else "language_server"

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_res = find_app_resources()

    if not app_res or not os.path.isdir(app_res):
        print(f"Error: Antigravity resources folder not found at: {app_res}")
        sys.exit(1)

    bin_name = get_binary_name()
    orig_bin = os.path.join(app_res, "bin", bin_name + ".orig")
    dest_bin = os.path.join(app_res, "bin", bin_name)
    target_bin = os.path.join(script_dir, "language_server_patched" + (".exe" if sys.platform == 'win32' else ""))
    bundle_dir = os.path.join(script_dir, "frontend_bundle")

    if not os.path.exists(orig_bin):
        if os.path.exists(dest_bin):
            print(f"Creating backup: {orig_bin}")
            shutil.copyfile(dest_bin, orig_bin)
        else:
            print(f"Error: Neither {dest_bin} nor {orig_bin} found!")
            sys.exit(1)

    print("1. Repacking localized frontend_bundle...")
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(bundle_dir):
            for file in sorted(files):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, bundle_dir)
                zf.write(full_path, rel_path)

    new_zip = zip_buf.getvalue()
    new_len = len(new_zip)

    print(f"Reading original binary: {orig_bin}")
    with open(orig_bin, 'rb') as f:
        data = bytearray(f.read())

    # Auto-detect embedded zip position
    eocd_pos = data.rfind(b'PK\x05\x06')
    if eocd_pos == -1:
        print("Error: Could not find ZIP EOCD signature in binary!")
        sys.exit(1)

    comment_len = int.from_bytes(data[eocd_pos+20:eocd_pos+22], 'little')
    cd_size = int.from_bytes(data[eocd_pos+12:eocd_pos+16], 'little')
    cd_offset = int.from_bytes(data[eocd_pos+16:eocd_pos+20], 'little')
    true_zip_start = eocd_pos - cd_size - cd_offset
    zip_end = eocd_pos + 22 + comment_len
    orig_len = zip_end - true_zip_start

    print(f"Original zip size: {orig_len} bytes (offset: {true_zip_start})")
    print(f"New zip size:      {new_len} bytes")

    if new_len > orig_len:
        print(f"Error: New zip ({new_len}) is larger than original ({orig_len})!")
        sys.exit(1)

    # Locate slice structure
    target_len_bytes = struct.pack('<Q', orig_len)
    slice_pos = -1
    for pos in range(0, len(data) - 24, 8):
        if data[pos+8:pos+16] == target_len_bytes and data[pos+16:pos+24] == target_len_bytes:
            ptr = struct.unpack('<Q', data[pos:pos+8])[0]
            if ptr & 0xFFFFFFFF == true_zip_start or (ptr >= true_zip_start and (ptr - true_zip_start) % 0x100000000 == 0):
                slice_pos = pos
                break

    if slice_pos == -1:
        print("Warning: Could not automatically detect slice struct; searching 32-bit offset...")
        for pos in range(0, len(data) - 16, 4):
            if data[pos:pos+4] == struct.pack('<I', true_zip_start):
                slice_pos = pos
                break

    print(f"Slice position located at: {slice_pos}")

    # Replace ZIP data in binary
    data[true_zip_start : true_zip_start + new_len] = new_zip
    if new_len < orig_len:
        data[true_zip_start + new_len : true_zip_start + orig_len] = b'\x00' * (orig_len - new_len)

    if slice_pos != -1:
        struct.pack_into('<Q', data, slice_pos + 8, new_len)   # len
        struct.pack_into('<Q', data, slice_pos + 16, new_len)  # cap

    with open(target_bin, 'wb') as f:
        f.write(data)

    os.chmod(target_bin, 0o755)

    if sys.platform == 'darwin':
        print("Ad-hoc codesigning patched binary on macOS...")
        subprocess.run(['codesign', '--force', '--deep', '--sign', '-', target_bin], check=True)

    print("Testing --stamp on patched binary...")
    res = subprocess.run([target_bin, '--stamp'], capture_output=True, text=True)
    if res.returncode != 0:
        print("Warning: --stamp returned non-zero:", res.stderr)
    else:
        print("Stamp output:", res.stdout.strip())

    print(f"Installing patched binary to {dest_bin}...")
    temp_dest = dest_bin + '.tmp'
    shutil.copyfile(target_bin, temp_dest)
    os.chmod(temp_dest, 0o755)
    if sys.platform == 'darwin':
        subprocess.run(['codesign', '--force', '--deep', '--sign', '-', temp_dest], check=True)
    os.replace(temp_dest, dest_bin)
    print("✓ Patched binary installed successfully!")

if __name__ == '__main__':
    main()
