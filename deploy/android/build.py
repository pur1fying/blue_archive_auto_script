#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import jinja2
import shutil
import typer
import subprocess
from typing import List

ARCH_MAP = {
    'arm64-v8a': {
        'p4a': 'arm64-v8a',
        'wheel': 'aarch64.whl',
    },
    'x86_64': {
        'p4a': 'x86_64',
        'wheel': 'x86_64.whl',
    },
}

DEFAULT_ARCH = 'arm64-v8a'
ANDROID_SDK_PATH = './.pyside6_android_deploy/android-sdk'
ANDROID_NDK_PATH = './.pyside6_android_deploy/android-ndk/android-ndk-r26b'
ICON_PATH = 'gui/assets/logo.png'
BIN_DIR = '.'
BUILD_DIR = 'build'
JARS_PATH = [
    'deploy/android/jar/PySide6/jar/Qt6Android.jar',
    'deploy/android/jar/PySide6/jar/Qt6AndroidBindings.jar'
]
PYSIDE6_WHEEL_BASIC_URL = 'https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.9.2-6.9.2-cp311-cp311-android_'
SHIBOKEN6_WHEEL_BASIC_URL = 'https://download.qt.io/official_releases/QtForPython/shiboken6/shiboken6-6.9.0-6.9.0-cp311-cp311-android_'
GRADLE_WRAPPER = '.buildozer/android/platform/build-arm64-v8a/dists/boa/gradlew'

def cwd_path(path: str):
    return os.path.abspath(os.path.join(os.getcwd(), path))

def self_path(path: str):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))

def proj_path(path: str):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', path))

def build_path(path: str):
    return os.path.abspath(os.path.join(proj_path(BUILD_DIR), path))

def log(msg: str):
    print(f'[{os.path.basename(__file__)}] {msg}')

def render(src: str, dst: str, ctx: dict):
    """Copy and/or render a file to a destination file."""
    if os.path.isfile(src):
        # Ensure destination directory exists
        dst_dir = os.path.dirname(dst)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        if '.templ.' in src:
            log(f'Rendering {src} to {dst}')
            with open(src, 'r') as f:
                template = jinja2.Template(f.read())
            with open(dst, 'w') as f:
                f.write(template.render(ctx))
        else:
            log(f'Copying {src} to {dst}')
            shutil.copy(src, dst)
    elif os.path.isdir(src):
        if not os.path.exists(dst):
            os.makedirs(dst)
        for root, dirs, files in os.walk(src):
            # Compute destination relative to the source directory to avoid absolute path join issues
            rel_root = os.path.relpath(root, src)
            for file in files:
                src_file = os.path.join(root, file)
                dst_root = dst if rel_root == '.' else os.path.join(dst, rel_root)
                dst_file = os.path.join(dst_root, file)
                if '.templ.' in dst_file:
                    dst_file = dst_file.replace('.templ', '')
                render(src_file, dst_file, ctx)
    else:
        raise FileNotFoundError(f'{src} not found')


def _configure(arch: str):
    if arch not in ARCH_MAP:
        raise typer.BadParameter(f'Unsupported arch: {arch}')
    arch_cfg = ARCH_MAP[arch]
    log('Reading requirements...')
    with open(self_path('requirements.txt'), 'r') as f:
        requirements = f.read()
    requirements = [line.strip() for line in requirements.splitlines() if line.strip()]
    log(f'Requirements: {requirements}')

    log('Generating buildozer.spec...')
    render(self_path('buildozer.templ.spec'), proj_path('buildozer.spec'), {
        'android_ndk_path': proj_path(ANDROID_NDK_PATH),
        'android_sdk_path': proj_path(ANDROID_SDK_PATH),
        'local_recipes_path': build_path('recipes'),
        'requirements': ','.join(requirements),
        'icon_path': proj_path(ICON_PATH),
        'bin_dir': proj_path(BIN_DIR),
        'jars_path': ','.join([proj_path(path) for path in JARS_PATH]),
        'p4a_hook_path': self_path('p4a_hook.py'),
        'android_archs': arch_cfg['p4a']
    })

    # Ensure build directory exists before downloading wheels and generating recipes
    os.makedirs(build_path(''), exist_ok=True)
    ensure_pyside6_shiboken6(arch_cfg)

def ensure_pyside6_shiboken6(arch):
    log('Check and download PySide6 wheels...')
    wheel_tag = arch['wheel']

    # download resource
    pyside6_path = build_path(f'PySide6-6.9.2-6.9.2-cp311-cp311-android_{wheel_tag}')
    pyside6_url = PYSIDE6_WHEEL_BASIC_URL + wheel_tag
    download_artifact(pyside6_path, pyside6_url)

    shiboken6_path = build_path(f'shiboken6-6.9.0-6.9.0-cp311-cp311-android_{wheel_tag}')
    shiboken6_url = SHIBOKEN6_WHEEL_BASIC_URL + wheel_tag
    download_artifact(shiboken6_path, shiboken6_url)

    log('Generating recipes...')
    if os.path.exists(build_path('recipes')):
        log(f'Removing existing recipes...')
        shutil.rmtree(build_path('recipes'))
    render(self_path('recipes'), build_path('recipes'), {
        'pyside6_wheel_path': pyside6_path,
        'shiboken6_wheel_path': shiboken6_path
    })

def download_artifact(path: str, url: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        log(f'Downloading artifact from to {path}...')
        os.system(f'curl -L {url} -o {path}')

def _build():
    os.environ['ANDROIDSDK'] = proj_path(ANDROID_SDK_PATH)
    os.environ['ANDROIDNDK'] = proj_path(ANDROID_NDK_PATH)
    os.system(f'buildozer android debug')

app = typer.Typer(help="Build helper for Android deployment")

@app.command()
def build():
    """Run the build step (calls buildozer)."""
    _build()

@app.command()
def gradle(args: List[str] = typer.Argument(None, help="Arguments passed to gradlew")):
    """Run the Gradle wrapper for the Android distribution.

    Any arguments after the command are passed directly to the `gradlew` wrapper.
    If no arguments are provided, `build` is used.
    Examples:
      python deploy/android/build.py gradle clean build
      python deploy/android/build.py gradle assembleRelease
    """
    gradle_path = proj_path(GRADLE_WRAPPER)
    if not os.path.exists(gradle_path):
        raise FileNotFoundError(f'Gradle wrapper not found: {gradle_path}')
    # Ensure it's executable
    try:
        st = os.stat(gradle_path).st_mode
        os.chmod(gradle_path, st | 0o111)
    except Exception:
        pass
    # Build command: default to 'build' when no args provided
    cmd = [gradle_path] + (list(args) if args else ['build'])
    log(f'Running gradle wrapper: {" ".join(cmd)}')
    cwd = os.path.dirname(gradle_path) or proj_path('.')
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    # copy output if exists
    output = '.buildozer/android/platform/build-arm64-v8a/dists/boa/build/outputs/apk/debug/boa-debug.apk'
    if os.path.exists(output):
        dst = proj_path('./boa-debug.apk')
        log(f'Copying APK to {dst}')
        shutil.copy(output, dst)

@app.command("all")
def all_cmd(
    arch: str = typer.Option(DEFAULT_ARCH, help="Android architecture (arm64-v8a, armeabi-v7a, x86_64)"),
    android_sdk_path: str = typer.Option(ANDROID_SDK_PATH, help="Android SDK path"),
    android_ndk_path: str = typer.Option(ANDROID_NDK_PATH, help="Android NDK path")
):
    """Run configure then build."""
    global ANDROID_SDK_PATH, ANDROID_NDK_PATH
    ANDROID_SDK_PATH = android_sdk_path
    ANDROID_NDK_PATH = android_ndk_path
    _configure(arch=arch)
    build()

if __name__ == '__main__':
    app()
