def test_legacy_service_installer_reuses_shared_implementation():
    from core.ocr.baas_ocr_client import server_installer
    from service import android_ocr_installer

    assert android_ocr_installer is server_installer
