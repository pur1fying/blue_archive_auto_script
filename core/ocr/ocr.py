from core.utils import is_android

if is_android():
    from .ocr_android import _Baas_ocr_android
    Baas_ocr = _Baas_ocr_android
else:
    from .ocr_pc import _Baas_ocr
    Baas_ocr = _Baas_ocr