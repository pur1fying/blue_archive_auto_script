#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import jinja2
import shutil

ANDROID_SDK_PATH = './.pyside6_android_deploy/android-sdk'
ANDROID_NDK_PATH = './.pyside6_android_deploy/android-ndk/android-ndk-r26b'
ICON_PATH = 'gui/assets/logo.png'
BIN_DIR = '.'
BUILD_DIR = 'build'
JARS_PATH = [
    'deploy/android/jar/PySide6/jar/Qt6Android.jar',
    'deploy/android/jar/PySide6/jar/Qt6AndroidBindings.jar'
]
PYSIDE6_WHEEL_URL = 'https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.9.2-6.9.2-cp311-cp311-android_aarch64.whl'
SHIBOKEN6_WHEEL_URL = 'https://download.qt.io/official_releases/QtForPython/shiboken6/shiboken6-6.9.0-6.9.0-cp311-cp311-android_aarch64.whl'

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

def configure():
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
        'jars_path': ','.join([proj_path(path) for path in JARS_PATH])
    })
    
    # Ensure build directory exists before downloading wheels and generating recipes
    os.makedirs(build_path(''), exist_ok=True)

    log('Check and download PySide6 wheels...')
    pyside6_path = build_path('PySide6-6.9.2-6.9.2-cp311-cp311-android_aarch64.whl')
    shiboken6_path = build_path('shiboken6-6.9.0-6.9.0-cp311-cp311-android_aarch64.whl')
    # Ensure parent directories exist for wheel paths
    os.makedirs(os.path.dirname(pyside6_path), exist_ok=True)
    os.makedirs(os.path.dirname(shiboken6_path), exist_ok=True)
    if not os.path.exists(pyside6_path):
        log(f'Downloading PySide6 wheel to {pyside6_path}...')
        os.system(f'curl -L {PYSIDE6_WHEEL_URL} -o {pyside6_path}')
    if not os.path.exists(shiboken6_path):
        log(f'Downloading Shiboken6 wheel to {shiboken6_path}...')
        os.system(f'curl -L {SHIBOKEN6_WHEEL_URL} -o {shiboken6_path}')

    log('Generating recipes...')
    if os.path.exists(build_path('recipes')):
        log(f'Removing existing recipes...')
        shutil.rmtree(build_path('recipes'))
    render(self_path('recipes'), build_path('recipes'), {
        'pyside6_wheel_path': pyside6_path,
        'shiboken6_wheel_path': shiboken6_path
    })

def build():
    os.environ['ANDROIDSDK'] = proj_path(ANDROID_SDK_PATH)
    os.environ['ANDROIDNDK'] = proj_path(ANDROID_NDK_PATH)
    os.system(f'buildozer android debug')

if __name__ == '__main__':
    configure()
    build()