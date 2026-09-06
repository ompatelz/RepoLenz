# Reproducible Web Packaging and CI Validation

## Overview

RepoLens embeds a complete static web application inside its Python package distribution.
To ensure that committed web distribution files never drift from the frontend source code,
Feature 6 introduces automated synchronization tooling and continuous integration verification.

## Implementation Details

1. **Synchronization and Verification Script (`scripts/sync_web_assets.py`)**:
   - `python scripts/sync_web_assets.py`: Cleans out stale hashed assets from
     `backend/repolens/web/assets/` and synchronizes fresh artifacts from `frontend/dist/`.
   - `python scripts/sync_web_assets.py --check`: Validates that every file in `frontend/dist/`
     matches the exact content of `backend/repolens/web/` without any stale or missing files,
     accounting for cross-platform line-ending normalization.

2. **Continuous Integration Check**:
   - The GitHub Actions `Frontend build` job runs `python3 scripts/sync_web_assets.py --check`
     immediately after building the frontend bundle.
   - Any commit that alters frontend source without updating packaged distribution assets
     will cleanly fail CI.

3. **Line Ending Consistency (`.gitattributes`)**:
   - Standardized `eol=lf` across repositories and web distribution artifacts to eliminate
     Windows CRLF normalization discrepancies.

4. **Automated Unit Tests**:
   - `tests/unit/api/test_web_assets.py` validates sync mechanics, drift detection, and extra
     file detection.
