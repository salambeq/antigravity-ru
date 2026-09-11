import os, sys, io, zipfile, struct, subprocess, shutil, time, signal

orig_bin = '/Applications/Antigravity.app/Contents/Resources/bin/language_server.orig'
target_bin = '/Users/Salambek/Antigravity Localization/language_server_patched'
dest_bin = '/Applications/Antigravity.app/Contents/Resources/bin/language_server'
bundle_dir = '/Users/Salambek/Antigravity Localization/frontend_bundle'

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
orig_len = 3212418
true_zip_start = 118051885

print(f"Original zip size: {orig_len} bytes")
print(f"New zip size:      {new_len} bytes")
if new_len > orig_len:
    print(f"ERROR: New zip ({new_len}) is larger than original ({orig_len})!")
    sys.exit(1)

print("2. Reading original binary...")
with open(orig_bin, 'rb') as f:
    data = bytearray(f.read())

print("3. Replacing ZIP data in binary...")
data[true_zip_start : true_zip_start + new_len] = new_zip
if new_len < orig_len:
    data[true_zip_start + new_len : true_zip_start + orig_len] = b'\x00' * (orig_len - new_len)

print("4. Updating Go slice struct at 146165872...")
slice_pos = 146165872
struct.pack_into('<Q', data, slice_pos + 8, new_len)   # len
struct.pack_into('<Q', data, slice_pos + 16, new_len)  # cap

print("5. Writing patched binary...")
with open(target_bin, 'wb') as f:
    f.write(data)

os.chmod(target_bin, 0o755)

print("6. Ad-hoc codesigning patched binary...")
subprocess.run(['codesign', '--force', '--deep', '--sign', '-', target_bin], check=True)

print("7. Testing --stamp on patched binary...")
res = subprocess.run([target_bin, '--stamp'], capture_output=True, text=True)
if res.returncode != 0:
    print("ERROR: --stamp failed!", res.stderr)
    sys.exit(1)
print("Stamp output:", res.stdout.strip())

print("8. Testing 2-second boot of patched binary...")
p = subprocess.Popen([
    target_bin,
    '--standalone',
    '--override_ide_name', 'antigravity',
    '--subclient_type', 'hub',
    '--override_ide_version', '2.12.2',
    '--override_user_agent_name', 'antigravity',
    '--https_server_port', '0',
    '--csrf_token', 'verify-token',
    '--app_data_dir', 'antigravity',
    '--api_server_url', 'https://generativelanguage.googleapis.com',
    '--cloud_code_endpoint', 'https://daily-cloudcode-pa.googleapis.com',
    '--enable_sidecars'
], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

time.sleep(2)
p.send_signal(signal.SIGINT)
stdout, stderr = p.communicate(timeout=5)
if "Starting language server" not in stderr:
    print("ERROR: Expected startup log not found in stderr:", stderr)
    sys.exit(1)
print("✓ Language server started and validated successfully!")

print("9. Installing patched binary to Application bundle...")
# Use atomic replace
temp_dest = dest_bin + '.tmp'
shutil.copyfile(target_bin, temp_dest)
os.chmod(temp_dest, 0o755)
subprocess.run(['codesign', '--force', '--deep', '--sign', '-', temp_dest], check=True)
os.replace(temp_dest, dest_bin)
print("✓ Patched language_server installed successfully!")
