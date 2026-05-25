from app.services.user_module.user_service.image_validation import detect_image_mime

_JPEG = b"\xff\xd8\xff" + b"\x00" * 10
_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
_WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 10
_UNKNOWN = b"FAKECONTENT"


def test_jpeg_detected() -> None:
    assert detect_image_mime(_JPEG) == "image/jpeg"


def test_png_detected() -> None:
    assert detect_image_mime(_PNG) == "image/png"


def test_webp_detected() -> None:
    assert detect_image_mime(_WEBP) == "image/webp"


def test_unknown_returns_none() -> None:
    assert detect_image_mime(_UNKNOWN) is None


def test_riff_non_webp_returns_none() -> None:
    data = b"RIFF\x00\x00\x00\x00AVI " + b"\x00" * 10
    assert detect_image_mime(data) is None
