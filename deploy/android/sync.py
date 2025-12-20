#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil
import tempfile
import argparse
from pathlib import Path

# ================= CONFIGURATION =================
PACKAGE_NAME = "top.qwq123.boa"
INTERNAL_SUB_DIR = "files/app" # 相对于 /data/data/top.qwq123.boa/
TEMP_DIR = "/data/local/tmp/"

# 新增：忽略列表 (文件夹名)
# 任何路径片段中包含这些名称的文件都会被完全忽略 (不推送，也不删除)
IGNORE_DIRS = {
    "__pycache__", 
    "_python_bundle",
    "p4a_env_vars.txt",
    "sitecustomize.py",
    "private.version",
    "libpybundle.version"
}
# =================================================

def get_adb_command():
    """Detect WSL and return the appropriate adb command."""
    if "microsoft" in platform.uname().release.lower():
        if shutil.which("adb.exe"):
            return "adb.exe"
    return "adb"

ADB_CMD = get_adb_command()

def should_ignore(path_str):
    """
    检查路径是否包含需要忽略的文件夹。
    path_str: 相对路径 (例如 core/ocr/__pycache__/cache.pyc)
    """
    # 统一分隔符
    p = path_str.replace("\\", "/")
    parts = p.split("/")
    
    # 如果路径中的任何一部分在忽略列表中，返回 True
    # 使用 set intersection 进行快速判断
    if set(parts).intersection(IGNORE_DIRS):
        return True
    return False

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0
    return f"{size:.{decimal_places}f} PB"

def run_cmd_capture(args, shell=False):
    try:
        res = subprocess.run(args, capture_output=True, text=True, check=True, shell=shell)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[!] Command failed: {args}\n    {e.stderr}")
        sys.exit(1)

def run_cmd_direct(args):
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError:
        print(f"[!] Failed to execute: {' '.join(args)}")
        sys.exit(1)

def check_run_as_access():
    cmd = [ADB_CMD, "shell", f"run-as {PACKAGE_NAME} id"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[!] Error: 'run-as {PACKAGE_NAME}' failed.")
            print("    Ensure the app is installed and debuggable=true in AndroidManifest.xml")
            sys.exit(1)
    except Exception as e:
        print(f"[!] ADB Error: {e}")
        sys.exit(1)

def get_local_files():
    """Get all local files (Main repo + Submodules) {relative_path: mtime(int)}."""
    print("[1/6] Scanning local git files (including submodules)...")
    files_map = {}

    # 1. Main repo
    cmd_main = ["git", "ls-files", "-c", "-o", "--exclude-standard"]
    out_main = run_cmd_capture(cmd_main)
    
    # 2. Submodules (recursive)
    cmd_sub = "git submodule foreach --quiet --recursive 'git ls-files -c -o --exclude-standard | sed \"s|^|$path/|\"'"
    try:
        out_sub = run_cmd_capture(cmd_sub, shell=True)
    except Exception:
        out_sub = "" 

    all_lines = out_main.splitlines() + out_sub.splitlines()

    for f in all_lines:
        f = f.strip()
        if not f: continue
        
        # === IGNORE CHECK ===
        if should_ignore(f):
            continue
        # ====================

        if os.path.exists(f) and os.path.isfile(f):
            files_map[f] = int(os.path.getmtime(f))
            
    return files_map

def get_remote_files():
    """Get remote files via run-as {relative_path: mtime(int)}."""
    print("[2/6] Fetching remote file status (via run-as)...")
    remote_map = {}
    
    find_cmd = f"cd {INTERNAL_SUB_DIR} && find . -type f -exec stat -c '%n|%Y' {{}} +"
    adb_args = [ADB_CMD, "shell", f"run-as {PACKAGE_NAME} sh -c \"{find_cmd}\""]
    
    try:
        res = subprocess.run(adb_args, capture_output=True, text=True)
        if res.returncode != 0:
            print("    -> Remote directory might not exist. Attempting to create...")
            subprocess.run([ADB_CMD, "shell", f"run-as {PACKAGE_NAME} mkdir -p {INTERNAL_SUB_DIR}"], stdout=subprocess.DEVNULL)
            return {}
            
        for line in res.stdout.splitlines():
            if "|" not in line: continue
            path, mtime = line.split("|")
            if path.startswith("./"): path = path[2:]
            clean_path = path.replace("\\", "/")
            
            # === IGNORE CHECK ===
            # 如果远程文件在忽略列表中，我们也假装没看见它（这样就不会触发删除逻辑）
            if should_ignore(clean_path):
                continue
            # ====================
            
            try:
                remote_map[clean_path] = int(float(mtime))
            except ValueError: pass
            
    except Exception as e:
        print(f"    -> Error fetching remote list: {e}")
        return {}
        
    return remote_map

def execute_delete_script(files_to_delete):
    """Generate script, push to tmp, exec via run-as."""
    if not files_to_delete: return
    
    print(f"[6/6] Executing deletion script ({len(files_to_delete)} files)...")
    
    script_name = "sync_delete_exec.sh"
    tmp_script_path = f"{TEMP_DIR}{script_name}"
    
    with open(script_name, "w", newline='\n', encoding='utf-8') as f:
        f.write("#!/bin/sh\n")
        f.write(f"cd {INTERNAL_SUB_DIR} || exit 1\n")
        for file_path in files_to_delete:
            f.write(f'rm -f "{file_path}"\n')
            
    try:
        run_cmd_direct([ADB_CMD, "push", script_name, tmp_script_path])
        print("    -> Running deletion inside app sandbox...")
        
        target_script = f"{INTERNAL_SUB_DIR}/{script_name}"
        
        cmd_exec = (
            f"cp {tmp_script_path} {target_script} && "
            f"chmod 777 {target_script} && "
            f"sh {target_script} && "
            f"rm {target_script}"
        )
        
        run_cmd_direct([ADB_CMD, "shell", f"run-as {PACKAGE_NAME} sh -c \"{cmd_exec}\""])
        run_cmd_capture([ADB_CMD, "shell", f"rm -f {tmp_script_path}"])
        
    finally:
        if os.path.exists(script_name):
            os.remove(script_name)

def print_changes(to_push, to_delete):
    print("\n" + "="*40)
    print("       SYNC PLAN (RUN-AS MODE)")
    print("="*40)
    if to_push:
        print(f"Files to PUSH ({len(to_push)}):")
        for f in to_push:
            print(f"  [+] {f}")
    else:
        print("Files to PUSH: None")
    print("-" * 20)
    if to_delete:
        print(f"Files to DELETE ({len(to_delete)}):")
        for f in to_delete:
            print(f"  [-] {f}")
    else:
        print("Files to DELETE: None")
    print("="*40 + "\n")

def sync(dry_run=False):
    check_run_as_access()
    
    local_map = get_local_files()
    remote_map = get_remote_files()
    
    to_push = []
    to_delete = []
    
    # Diff Logic
    for f_path, l_mtime in local_map.items():
        remote_path = f_path.replace("\\", "/") 
        if remote_path not in remote_map:
            to_push.append(f_path)
        else:
            r_mtime = remote_map[remote_path]
            if l_mtime != r_mtime:
                to_push.append(f_path)

    local_paths_linux = set(p.replace("\\", "/") for p in local_map.keys())
    for r_path in remote_map.keys():
        if r_path not in local_paths_linux:
            to_delete.append(r_path)

    print_changes(to_push, to_delete)

    if dry_run:
        print("[DRY RUN] No changes were applied.")
        return

    if not to_push and not to_delete:
        print("[√] Already up to date.")
        return

    # Push
    if to_push:
        print("[3/6] Packing files...")
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tmp_list:
            tmp_list.write('\n'.join(to_push))
            tmp_list_path = tmp_list.name
            
        tar_name = "sync_update.tar"
        tar_tmp_path = f"{TEMP_DIR}{tar_name}"
        
        try:
            run_cmd_capture(["tar", "-cf", tar_name, "-T", tmp_list_path])
            tar_size = os.path.getsize(tar_name)
            readable_size = human_readable_size(tar_size)

            print(f"[4/6] Pushing to temp: {tar_name} ({readable_size})...")
            run_cmd_direct([ADB_CMD, "push", tar_name, tar_tmp_path])
            
            print("    -> Extracting into App Data (via run-as)...")
            cmd_extract = (
                f"mkdir -p {INTERNAL_SUB_DIR} && "
                f"tar -xf {tar_tmp_path} -C {INTERNAL_SUB_DIR}"
            )
            run_cmd_direct([ADB_CMD, "shell", f"run-as {PACKAGE_NAME} sh -c \"{cmd_extract}\""])
            run_cmd_capture([ADB_CMD, "shell", f"rm -f {tar_tmp_path}"])
            
        finally:
            if os.path.exists(tmp_list_path): os.remove(tmp_list_path)
            if os.path.exists(tar_name): os.remove(tar_name)
    else:
        print("[3/6] No files to update (Push skipped).")

    # Delete
    execute_delete_script(to_delete)
    
    print("\n[√] Sync Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync local Git files to Android App Data via ADB run-as")
    parser.add_argument("--dry-run", action="store_true", help="List changes without executing them")
    args = parser.parse_args()

    if ADB_CMD == "adb.exe":
        print("[*] WSL Environment Detected: Using host adb.exe")
        
    sync(dry_run=args.dry_run)