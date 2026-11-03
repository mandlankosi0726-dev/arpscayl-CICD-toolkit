# Python API starter

This small standard-library example demonstrates the toolkit's Python CI consumer. Replace `your-org` in `.github/workflows/ci.yml` with the toolkit repository owner, then pin a published toolkit release. The reusable workflow installs packages in `requirements.txt`, runs Ruff and pytest, enforces the configured coverage threshold, and uploads test reports. The Python code is a testable API domain stub; add an HTTP framework only when the project needs one.

Run `python -m pip install pytest pytest-cov ruff`, then `PYTHONPATH=src python -m pytest` locally. Add application dependencies to `requirements.txt` with reviewed version pins.
