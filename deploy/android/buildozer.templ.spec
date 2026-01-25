[app]
title = Baas on Android
package.name = boa
package.domain = top.qwq123
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,qml,js,json,txt,apk
source.exclude_patterns = deploy,boa-*.apk
android.whitelist = *.apk
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
p4a.url = https://github.com/XcantloadX/python-for-android.git
p4a.branch = develop
p4a.commit = e05b63b47dbd9bc8da54228c28d5cc7fea822672
p4a.bootstrap = qt
p4a.local_recipes = {{ local_recipes_path }}
android.permissions = android.permission.WRITE_EXTERNAL_STORAGE, android.permission.INTERNET, android.permission.INTERACT_ACROSS_USERS_FULL
android.add_jars = {{ jars_path }}
p4a.extra_args = --qt-libs=Core,Gui,Widgets --load-local-libs=plugins_platforms_qtforandroid --init-classes=
icon.filename = {{ icon_path }}
android.enable_androidx = True
android.entrypoint = org.baas.boa.MainActivity

######### Shizuku #########
android.gradle_dependencies = dev.rikka.shizuku:api:13.1.5,dev.rikka.shizuku:provider:13.1.5,androidx.core:core:1.6.0,org.jetbrains.kotlin:kotlin-stdlib:1.9.22
# ps: androidx is not required by shizuku
p4a.hook = {{ p4a_hook_path }}
android.no-byte-compile-python = True

######### RapidOCR #########
android.add_aars = {{ rapidocr_aar_path }}
android.add_gradle_repositories = flatDir { dirs '{{ rapidocr_dir_path }}' }

[buildozer]
log_level = 2
warn_on_root = 1
bin_dir = {{ bin_dir }}

