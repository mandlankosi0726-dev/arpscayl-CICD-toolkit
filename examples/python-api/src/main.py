"""Small standard-library API domain example."""


def health_status() -> dict[str, str]:
    """Return a minimal health payload suitable for a later HTTP handler."""
    return {"status": "ok"}
