# This Directory contains the installer (Artifact for executable) for the project.

`installer.py` is the single source entry point for installation, updates, launching,
and PyInstaller builds on Windows and Linux. Run it from the repository root with
`python deploy/installer/installer.py` or `python -m deploy.installer.installer`.
Its configuration remains in `setup.toml`; dynamic updates and launcher rebuilding
use this same file.

**To use the installer, you need to have the following installed on your system:**

- **Python 3.6 or higher, recommendation is version 3.10.11**

## Maunal

1. For `Windows` users, please double click on the `build.bat` file.
2. For `Linux` users, run the following command in the terminal:
    ```bash
    $ bash ./build.sh
    ```
   Note that you have to run the script on filesystem that supports `chmod +x` command.
3. The installer will be generated in the Current Directory.
