import os
import shutil
from pythonforandroid.logger import info

PATCH_MANIFEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shizuku_provider.xml')
FRAG_BUILD_GRADLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patches', 'frag.build.gradle')
JAVA_SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'main', 'java')
AIDL_SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'main', 'aidl')

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
    # insert after android {
    content = content.replace('android {', 'android {\n' + build_gradle)
    _write(build_gradle_path, content)
    info(f'Successfully patched {build_gradle_path} with frag build.gradle.')

def _patch_manifest(manifest_path: str):
    info(f'Patching manifest: {manifest_path}')
    with open(manifest_path, 'r', encoding='utf-8') as f:
        content = f.read()

    with open(PATCH_MANIFEST_PATH, 'r', encoding='utf-8') as f:
        provider_xml = f.read()

    # Insert the provider XML before the closing </application> tag
    marker = '</application>'
    if marker in content:
        parts = content.rsplit(marker, 1)
        content = f'{parts[0]}{provider_xml}\n{marker}{parts[1]}'
    else:
        raise ValueError(f"Could not find '{marker}' in {manifest_path}")

    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(content)
    info(f'Successfully patched {manifest_path} with Shizuku provider.')

def _copy_src():
    info(f'Copying java src: from {JAVA_SRC_PATH} to {os.path.join(os.getcwd(), "./src/main/java")}')
    shutil.copytree(JAVA_SRC_PATH, './src/main/java', dirs_exist_ok=True)
    info(f'Copying aidl src: from {AIDL_SRC_PATH} to {os.path.join(os.getcwd(), "./src/main/aidl")}')
    shutil.copytree(AIDL_SRC_PATH, './src/main/aidl', dirs_exist_ok=True)
    info(f'Successfully copied {JAVA_SRC_PATH} and {AIDL_SRC_PATH} to src/main/java and src/main/aidl.')


def before_apk_assemble(toolchain):
    info(f'pwd: {os.getcwd()}')
    manifest1 = os.path.join('.', 'AndroidManifest.xml')
    manifest2 = os.path.join('.', 'src', 'main', 'AndroidManifest.xml')
    build_gradle = os.path.join('.', 'build.gradle')
    
    _patch_build_gradle(build_gradle)
    _patch_manifest(manifest1)
    _patch_manifest(manifest2)
    _copy_src()