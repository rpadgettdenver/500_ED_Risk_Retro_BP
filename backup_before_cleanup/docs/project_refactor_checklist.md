# 🛠️ Refactor Plan
Based on GPT-4's project audit, here are suggested improvements to the project structure, code organization, and quality:

## ✅ Folder Structure and File Layout
- [ ] Rename base directory from `500_ED_Risk_Retro_BP` to something more descriptive like `EnergizeDenver_RiskRetrofit`.
- [ ] Standardize file and directory naming conventions (e.g., use consistent `snake_case`).
- [ ] Ensure clear separation of concerns between `src`, `scripts`, and `docs`.
- [ ] Remove versioning from filenames (use Git history instead).
- [ ] Remove hardcoded absolute paths; use relative paths and env vars.
- [ ] Move any outdated files to an `archive/` folder outside `src/`.

## 🧩 Modularity and Code Organization
- [ ] Add useful imports to empty `__init__.py` files to expose public APIs.
- [ ] Ensure all modules use the centralized configuration system.
- [ ] Make utility functions in `utils` generic and reusable.
      _Reason: Promote modularity and reduce duplication across scripts and modules._
- [ ] Ensure `data_processing` contains only ETL logic, not business rules.
- [ ] Separate financial models from business logic in `models`.
- [ ] Verify `gcp/` handles credentials securely using env vars.
- [ ] Use `data_processing` helpers in `analytics/` scripts for consistency.
- [ ] Add or update docstrings for all modules, functions, and classes.
- [ ] Keep `docs/` folder up to date with project documentation.
- [ ] Document all scripts in `scripts/` with usage instructions.
- [ ] Add a `tests/` directory with unit tests for key modules.

## 🔧 General Improvements
- [ ] Set up a centralized logging system.
- [ ] Improve error handling and exception logging throughout.
- [ ] Optimize for performance where needed (e.g. use async/parallel).
- [ ] Encourage regular code reviews (if collaborative).
- [ ] Add CI/CD pipeline (e.g. GitHub Actions).
- [ ] Use `requirements.txt` or `Pipfile` for dependency management.
- [ ] Enforce consistent formatting with `flake8`, `black`, or similar.
- [ ] Audit for potential security vulnerabilities.
