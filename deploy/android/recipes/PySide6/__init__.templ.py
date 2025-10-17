# Copyright (C) 2023 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import shutil
import zipfile
from pathlib import Path

from pythonforandroid.logger import info
from pythonforandroid.recipe import PythonRecipe


class PySideRecipe(PythonRecipe):
    version = '6.9.2'
    wheel_path = '{{ pyside6_wheel_path }}'
    depends = ["shiboken6"]
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def build_arch(self, arch):
        """Unzip the wheel and copy into site-packages of target"""

        info("Copying libc++_shared.so from SDK to be loaded on startup")
        libcpp_path = f"{self.ctx.ndk.sysroot_lib_dir}/{arch.command_prefix}/libc++_shared.so"
        shutil.copyfile(libcpp_path, Path(self.ctx.get_libs_dir(arch.arch)) / "libc++_shared.so")

        info(f"Installing {self.name} into site-packages")
        with zipfile.ZipFile(self.wheel_path, "r") as zip_ref:
            info("Unzip wheels and copy into {}".format(self.ctx.get_python_install_dir(arch.arch)))
            zip_ref.extractall(self.ctx.get_python_install_dir(arch.arch))

        lib_dir = Path(f"{self.ctx.get_python_install_dir(arch.arch)}/PySide6/Qt/lib")

        info("Copying Qt libraries to be loaded on startup")
        shutil.copytree(lib_dir, self.ctx.get_libs_dir(arch.arch), dirs_exist_ok=True)
        shutil.copyfile(lib_dir.parent.parent / "libpyside6.abi3.so",
                        Path(self.ctx.get_libs_dir(arch.arch)) / "libpyside6.abi3.so")

          # noqa: E999
        shutil.copyfile(lib_dir.parent.parent / f"QtCore.abi3.so",
                        Path(self.ctx.get_libs_dir(arch.arch)) / "QtCore.abi3.so")
          # noqa: E999
          # noqa: E999
        shutil.copyfile(lib_dir.parent.parent / f"QtGui.abi3.so",
                        Path(self.ctx.get_libs_dir(arch.arch)) / "QtGui.abi3.so")
          # noqa: E999
          # noqa: E999
        shutil.copyfile(lib_dir.parent.parent / f"QtWidgets.abi3.so",
                        Path(self.ctx.get_libs_dir(arch.arch)) / "QtWidgets.abi3.so")
          # noqa: E999
          # noqa: E999

          # noqa: E999

          # noqa: E999
        plugin_path = (lib_dir.parent / "plugins" / "platforms" /
                      f"libplugins_platforms_qtforandroid_{arch.arch}.so")
        if plugin_path.exists():
            shutil.copyfile(plugin_path,
                            (Path(self.ctx.get_libs_dir(arch.arch)) /
                             f"libplugins_platforms_qtforandroid_{arch.arch}.so"))
          # noqa: E999


recipe = PySideRecipe()