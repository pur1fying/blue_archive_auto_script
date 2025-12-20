#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil
import tempfile
import argparse
import fnmatch

# ================= CONFIGURATION =================
PACKAGE_NAME = "top.qwq123.boa"
INTERNAL_SUB_DIR = "files/app" # 相对于 /data/data/top.qwq123.boa/
TEMP_DIR = "/data/local/tmp/"

# --- 1. 白名单 (SYNC_WHITELIST) ---
# 只有匹配这些规则的文件才会被扫描和同步。
# 语法参考 gitignore：
# - "dir/"       : 匹配目录及其子内容
# - "*.py"       : 匹配后缀
# - "path/to/f"  : 匹配具体文件
SYNC_WHITELIST = [
    "/core/",
    # "/core/Baas_thread.py",
    "/main.py",
    "/window.py",
]

# --- 2. 黑名单 (SYNC_BLACKLIST) ---
# 任何匹配这些规则的文件都会被强制排除。
# (既不会被推送到手机，远程存在的也不会被删除，视为“隐形”文件)
SYNC_BLACKLIST = [
    "__pycache__/",
    "*.pyc",
    ".git/",
    ".github/",
    "tests/",
    "*.log",
    ".DS_Store",
    "/core/ocr/baas_ocr_client/bin/"
]
# =================================================

def get_adb_command():
    """Detect WSL and return the appropriate adb command."""
    if "microsoft" in platform.uname().release.lower():
        if shutil.which("adb.exe"):
            return "adb.exe"
    return "adb"

ADB_CMD = get_adb_command()

def match_path(path, patterns):
    """
    检查路径是否匹配给定的模式列表。
    支持以 "/" 开头锚定根目录，支持以 "/" 结尾匹配目录及其子内容。
    """
    # 统一路径分隔符为 Linux 风格
    path = path.replace("\\", "/")
    path_parts = path.split("/")
    filename = os.path.basename(path)

    for pat in patterns:
        if not pat or pat.startswith('#'): continue
        
        # === 情况 A: 根目录锚定 (以 / 开头) ===
        if pat.startswith("/"):
            # 去掉开头的 /，变成 "core/" 或 "main.py"
            clean_pat = pat[1:]
            
            # 1. 如果是目录规则 (例如 "/core/")
            if clean_pat.endswith("/"):
                # 逻辑：只要当前文件路径是以 "core/" 开头的，
                # 无论它多深 (例如 core/sub/a.py)，startswith 都会返回 True
                if path.startswith(clean_pat):
                    return True
            
            # 2. 如果是文件规则 (例如 "/main.py")
            else:
                # 精确全路径匹配
                if path == clean_pat:
                    return True
                # 或者处理通配符 (例如 "/build/*.txt")
                if fnmatch.fnmatch(path, clean_pat):
                    return True
        
        # === 情况 B: 宽松匹配 (不以 / 开头) ===
        else:
            # 1. 目录匹配 (例如 "assets/") -> 匹配任意深度的 assets 文件夹
            if pat.endswith("/"):
                clean_pat = pat.rstrip("/")
                if clean_pat in path_parts:
                    return True
            
            # 2. 普通文件/通配符匹配 (例如 "*.py")
            else:
                if "/" in pat:
                    if fnmatch.fnmatch(path, pat):
                        return True
                else:
                    if fnmatch.fnmatch(filename, pat):
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
    """Get all local files filtered by inline whitelist and blacklist."""
    print("[1/6] Scanning local git files and filtering...")
    files_map = {}

    # 1. Main repo (Git files)
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
        
        # === 核心过滤逻辑 ===
        # 1. 必须在白名单中
        if not match_path(f, SYNC_WHITELIST):
            continue
        
        # 2. 必须不在黑名单中
        if match_path(f, SYNC_BLACKLIST):
            continue
        # ===================

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
            
            # === [FIX] 远程文件过滤逻辑修正 ===
            
            # 1. 必须不在黑名单中 (保持原逻辑：保护黑名单文件不被操作)
            if match_path(clean_path, SYNC_BLACKLIST):
                continue

            # 2. [新增] 必须在白名单中
            # 如果远程文件根本不在白名单范围内（例如 build/ 产物），我们假装没看见它。
            # 这样它就不会进入 remote_map，从而不会触发“本地无此文件 -> 删除”的逻辑。
            if not match_path(clean_path, SYNC_WHITELIST):
                continue
            
            # ===============================
            
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
    
    if not SYNC_WHITELIST:
        print("[!] Warning: SYNC_WHITELIST is empty. No files will be synced.")
    
    # 1. Get filtered local and remote files
    local_map = get_local_files()
    remote_map = get_remote_files()
    
    to_push = []
    to_delete = []
    
    # 2. Diff Logic
    # PUSH
    for f_path, l_mtime in local_map.items():
        remote_path = f_path.replace("\\", "/") 
        if remote_path not in remote_map:
            to_push.append(f_path)
        else:
            r_mtime = remote_map[remote_path]
            if l_mtime != r_mtime:
                to_push.append(f_path)

    # DELETE
    # remote_map 现在只包含“白名单内”且“非黑名单”的文件
    # 如果它在 remote_map 中，但在 local_map 中找不到，说明它在本地被删除了（或者是旧的残留文件），应该删除。
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
            # -T takes the file list
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
    parser = argparse.ArgumentParser(description="Sync whitelist-based local files to Android App Data")
    parser.add_argument("--dry-run", action="store_true", help="List changes without executing them")
    args = parser.parse_args()

    if ADB_CMD == "adb.exe":
        print("[*] WSL Environment Detected: Using host adb.exe")
        
    sync(dry_run=args.dry_run)