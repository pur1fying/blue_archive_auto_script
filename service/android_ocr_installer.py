"""Compatibility import for the shared OCR installer.

The service and desktop launchers use the same installer and OCR paths. Keep
this old module path available without maintaining a second implementation.
"""
import sys

from core.ocr.baas_ocr_client import server_installer

sys.modules[__name__] = server_installer
