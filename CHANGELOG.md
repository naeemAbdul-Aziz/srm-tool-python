## Changelog

All notable changes to this project will be documented in this file.

The format loosely follows Keep a Changelog principles.

### [Unreleased]
- WebSocket/SSE push notifications
- Admin notification compose UI
- Analytics QA automation script
- Performance tracking instrumentation
#### Added
- `/auth/me` endpoint for lightweight credential verification and client session introspection.
#### Changed
- Refactored `/notifications/stream` to load after authentication dependency definitions and now using `Depends(get_current_user)` for consistent Basic auth handling.
- Internal module import strategy refactored: all intra-backend imports now use package-relative form with safe absolute fallbacks to support both `uvicorn backend.api:app` (project root) and `python backend/main.py` from root or inside the `backend` directory. Added adaptive startup logic in `backend/main.py` that adjusts `sys.path` when invoked from inside the package.
#### Fixed
- Incorrect FastAPI dependency usage (`Depends(authenticate_user)`) on assessments and notification CRUD endpoints causing authentication failures/422 errors. Replaced with proper `Depends(get_current_user)` wrapper (SSE stream kept on direct `authenticate_user` until refactor of definition order).
- Startup ImportError (`attempted relative import with no known parent package`) when launching with relative imports but using non-package execution context. Resolved by enforcing fully qualified uvicorn target and adaptive path injection.

### [2.1.2] - 2025-10-06
#### Added
- Unified multi-format summary export streaming helper (`build_summary_file`) consolidating PDF, TXT, CSV generation.
- Frontend support for new download buttons (PDF, TXT, Excel, CSV) with improved accessibility attributes.
- Reference-counted global loading spinner utilities (`showLoading`, `hideLoading`, `withGlobalLoading`).
- Analytics validation harness script (`analytics_validation.py`) groundwork for dashboard QA.
- Extensive seeding refactor: extracted static data to `seed_constants.py` and generation utilities to `seed_helpers.py` for maintainability.
- Modular frontend components (`js/components/assessments.js`, `js/components/notifications.js`).

#### Changed
- Summary report endpoints now return direct binary streaming responses (removed fragile temp file reads) for PDF/TXT/CSV; Excel path retained with in-memory workbook.
- Dashboard analytics field mapping fixed to use `total_count` keys (frontend `updateDashboardUI` adjustments).
- Notification UI greatly expanded (bell, dropdown panel, composer scaffold, pagination hooks, SSE integration attempt).
- Improved download UX: dynamic button state text ("Downloading ..."), resilient filename extraction, fallback manual link injection.

#### Fixed
- Broken non-Excel report exports (now functional for PDF, TXT, CSV via unified builder).
- Duplicate / overlapping loading spinner issue by introducing `.local-spinner` and singleton global spinner.
- Potential empty-content Excel download race by adding size checks and delayed cleanup.
- Removed committed generated artifacts (logs, PDFs, CSV/XLSX sample files) and updated `.gitignore` to prevent reintroduction.

#### Removed
- Generated artifacts previously tracked: summary/personal report PDFs, sample CSV/XLSX, transient logs.

#### Maintenance
- Repository hygiene pass (artifact purge + ignore rules) preparing for clean release.
- Documentation synchronized (`PROJECT_STATUS.md` reflects report formats & notification phase).

#### Notes
- Next release will focus on real-time push notifications (SSE/WebSocket finalization) and analytics QA automation integration.


### [2.1.1] - 2025-10-06
#### Added
- Admin personal academic report endpoint: `GET /admin/reports/personal/{student_index}?format=txt|pdf` (mirrors student self-service endpoints, used by export tests)
- Documentation updates for simplified role model (admin & student only) and deterministic student password scheme

#### Changed
- Seeding docs clarified: only core `admin` user created by default; optional legacy demo admins (registrar/dean) gated behind `SEED_EXTRA_ADMINS=true`
- README and Quick Reference corrected to remove stale JWT references (system uses HTTP Basic + bcrypt)

#### Fixed
- Frontend duplicate loading spinner (overlapping global + modal) resolved via distinct `.local-spinner` class
- Export documentation aligned with implemented multi-format summary + personal report endpoints
- Minor typos and encoding artifact in backend README

### [2.1.0] - 2025-10-05
#### Added
- Streaming Excel summary export (`/admin/reports/summary/excel`) with multi-sheet workbook (Summary, GradeDistribution)
- Notification Center Phase 1 (backend tables, endpoints, frontend bell, unread badge, mark read/all)
- Documentation updates: `PROJECT_STATUS.md`, `STARTUP_GUIDE.md`, `backend/QUICK_REFERENCE.md`, `SRMS_IMPROVEMENTS.md`
- `CHANGELOG.md` file created

#### Changed
- Reworked Excel generation from temp file approach to in-memory BytesIO with explicit headers
- Enhanced report header exposure and reliability for file downloads

#### Fixed
- Malformed `TABLES` dict causing syntax issues
- Missing import comma in `api.py` import block
- Excel download failure (was returning wrapped JSON first) now direct binary

### [2.0.0] - 2025-10-01
#### Added
- Enhanced analytics dashboard (grade distribution, GPA trends, course stats)
- Advanced search and filtering improvements

#### Notes
- Initial groundwork for notification system planning

---

Prior history intentionally condensed; earlier versions focused on core CRUD, authentication, and PDF/TXT reporting foundations.
