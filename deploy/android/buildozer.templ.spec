[app]
title = Baas on Android
package.name = boa
package.domain = top.qwq123
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,qml,js,json,txt
version = 0.1
# NOTE: requirements 列表不可以写成多行，否则构建时会因为 bug 出错
requirements = {{ requirements }}
orientation = landscape
fullscreen = 1
android.archs = arm64-v8a
android.allow_backup = True
android.minapi = 24
android.ndk_path = {{ android_ndk_path }}
android.sdk_path = {{ android_sdk_path }}
p4a.bootstrap = qt
p4a.local_recipes = {{ local_recipes_path }}
p4a.branch = develop
android.permissions = android.permission.WRITE_EXTERNAL_STORAGE, android.permission.INTERNET
android.add_jars = {{ jars_path }}
p4a.extra_args = --qt-libs=Core,Gui,Widgets --load-local-libs=plugins_platforms_qtforandroid --init-classes=
icon.filename = {{ icon_path }}

[buildozer]
log_level = 2
warn_on_root = 1
bin_dir = {{ bin_dir }}

