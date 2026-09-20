# Contributing to Smart Home Known Issues

Thank you for your interest in contributing! Whether you're reporting bugs, improving documentation, or submitting pull requests, your help is welcome.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Qballjos/homey_known_issue_page.git
   cd homey_known_issue_page
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the local test suite:**
   ```bash
   PYTHONPATH=. pytest
   ```

5. **Start the local dev server:**
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```

## Pull Request Guidelines

- Ensure all new features or bug fixes are covered by tests in `tests/`.
- Verify that `pytest` passes with 0 failures before submitting.
- Follow PEP 8 style conventions and keep functions modular and focused.
- Commit messages should follow the [Conventional Commits](https://www.conventionalcommits.org/) format (e.g., `feat: ...`, `fix: ...`, `docs: ...`).
