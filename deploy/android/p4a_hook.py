import os
import shutil
from pythonforandroid.logger import info

# 脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PATCH_MANIFEST_PATH = os.path.join(BASE_DIR, 'shizuku_provider.xml')
FRAG_BUILD_GRADLE_PATH = os.path.join(BASE_DIR, 'patches', 'frag.build.gradle')
JAVA_SRC_PATH = os.path.join(BASE_DIR, 'src', 'main', 'java')
AIDL_SRC_PATH = os.path.join(BASE_DIR, 'src', 'main', 'aidl')
CRASH_MANIFEST_PATH = os.path.join(BASE_DIR, 'crash_manifest.xml')
PROVIDER_PATHS_SRC = os.path.join(BASE_DIR, 'provider_paths.xml')

def _read(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def _write(path: str, content: str):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def _patch_build_gradle(build_gradle_path: str):
    info(f'Patching build.gradle: {build_gradle_path}')
    content = _read(build_gradle_path)
    build_gradle = _read(FRAG_BUILD_GRADLE_PATH)
    content = content.replace('android {', 'android {\n' + build_gradle)
    _write(build_gradle_path, content)
    info(f'Successfully patched {build_gradle_path} with frag build.gradle.')

def _patch_manifest(manifest_path: str):
    info(f'Patching manifest: {manifest_path}')
    content = _read(manifest_path)

    # 读取 Shizuku 配置
    inject_content = ""
    inject_content += _read(PATCH_MANIFEST_PATH)

    # [NEW 2] 追加读取 CrashActivity 和 Provider 配置
    inject_content += "\n" + _read(CRASH_MANIFEST_PATH)

    marker = '</application>'
    if marker in content:
        # 简单防重复
        if 'CrashActivity' not in content:
            parts = content.rsplit(marker, 1)
            content = f'{parts[0]}{inject_content}\n{marker}{parts[1]}'
        else:
            info("CrashActivity already present in manifest, skipping injection.")
    else:
        raise ValueError(f"Could not find '{marker}' in {manifest_path}")

    _write(manifest_path, content)
    info(f'Successfully patched {manifest_path}.')

def _copy_src():
    # 复制 Java
    info(f'Copying java src...')
    shutil.copytree(JAVA_SRC_PATH, './src/main/java', dirs_exist_ok=True)
    
    # 复制 AIDL
    info(f'Copying aidl src...')
    shutil.copytree(AIDL_SRC_PATH, './src/main/aidl', dirs_exist_ok=True)
    
    # [NEW 3] 复制 FileProvider 的资源文件 (关键修复步骤)
    # 目标路径必须是 src/main/res/xml/
    target_res_xml = os.path.join(os.getcwd(), 'src', 'main', 'res', 'xml')
    if not os.path.exists(target_res_xml):
        os.makedirs(target_res_xml)
    shutil.copy(PROVIDER_PATHS_SRC, target_res_xml)
    info(f'Successfully copied provider_paths.xml to {target_res_xml}')

def before_apk_assemble(toolchain):
    info(f'pwd: {os.getcwd()}')
    manifest1 = os.path.join('.', 'AndroidManifest.xml')
    manifest2 = os.path.join('.', 'src', 'main', 'AndroidManifest.xml')
    build_gradle = os.path.join('.', 'build.gradle')
    
    _patch_build_gradle(build_gradle)
    _patch_manifest(manifest1)
    _patch_manifest(manifest2)
    _copy_src()