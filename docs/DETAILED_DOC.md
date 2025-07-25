# Student Result Management Tool - Technical Documentation

## Overview
This document provides a detailed technical breakdown of the Student Result Management Tool, covering all modules, functions, data flow, error handling, extensibility, and example workflows.

---

## 1. Architecture & Data Flow
- Modular Python CLI app.
- PostgreSQL database backend.
- File import/export (CSV/TXT, GUI/CLI).
- Logging to `app.log`.
- Reports generated in TXT and PDF formats.

---

## 2. Module-by-Module Breakdown

### main.py
- Entry point.
- Connects to DB, creates tables, launches menu.
- Function: `main()`

### menu.py
- CLI menu logic.
- Handles user input, routes to features.
- Functions: `show_menu()`, `run_menu()`

### db.py
- DB connection, table creation, insert/update, fetch.
- Functions: `connect_to_db()`, `create_tables()`, `insert_student_record()`, `fetch_all_records()`
- Rollback on error for all write operations.

### file_handler.py
- File parsing, validation, and import.
- Functions: `is_valid_record()`, `parse_record()`, `read_student_file()`, `process_file_and_insert()`

### grading.py
- Grade calculation and summary.
- Functions: `calculate_grade()`, `summarize_grades()`

### report_utils.py
- TXT/PDF report generation, sorting by name then grade.
- Functions: `export_summary_report_txt()`, `export_summary_report_pdf()`

### logger.py
- Logging setup for all modules.
- Function: `get_logger()`

### config.py
- Stores DB credentials as constants.

### auth.py
- Placeholder for authentication/user management.

### gui_file_loader.py
- Tkinter GUI for file selection and import.
- Function: `select_file_and_load()`

---

## 3. Function/Class Descriptions
- Each function is documented inline in code with docstrings.
- All modules use clear, descriptive names and parameters.

---

## 4. Error Handling
- All DB write operations use try/except and rollback.
- Errors are logged to `app.log`.
- User-facing errors are printed in CLI/GUI.

---

## 5. Extensibility
- Add new features by creating new modules or extending existing ones.
- Follow modular design and error handling patterns.
- Use logger for all new modules.

---

## 6. Example Workflows

### Add a Student
- Use CLI menu option 6 or import from file.
- Data validated, grade calculated, record inserted into DB.

### Update a Student Score
- Use CLI menu option 3.
- Enter index number and new score.
- Grade recalculated, record updated in DB.

### Export Summary Report
- Use CLI menu option 4 (TXT) or 5 (PDF).
- Report sorted by name, then grade.

### Import Students from File
- Use CLI menu option 8 (GUI).
- Select file, records validated and inserted.

---

## 7. Data Formats
- CSV/TXT: `index_number, full_name, course, score`
- DB: See `docs/DB_SCHEMA.md`
- Reports: Human-readable TXT/PDF

---

## 8. Logging
- All modules use `logger.py` for logging.
- Log file: `app.log`
- Log format: timestamp, level, message

---

## 9. Security & Authentication
- Basic user table in DB.
- `auth.py` is a template for future authentication features.

---

## 10. Testing & Validation
- Manual testing via CLI menu and file import.
- Validate file formats and DB connection before use.

---

## 11. Further Reading
- See `README.md` for high-level overview.
- See `docs/DB_SCHEMA.md` for database details.
- See `docs/USAGE_GUIDE.md` for step-by-step usage.

---

## 12. Contact & Support
- For issues, see `docs/FAQ.md` or open a GitHub issue.
