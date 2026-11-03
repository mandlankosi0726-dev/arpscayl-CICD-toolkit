from main import health_status


def test_health_status() -> None:
    assert health_status() == {"status": "ok"}
