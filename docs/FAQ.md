# Frequently Asked Questions (FAQ)

## General

**Q: What is this tool for?**
A: Managing student results, grades, and generating summary reports.

**Q: What platforms are supported?**
A: Windows, macOS, Linux (Python 3.8+ required).

## Database

**Q: What database is used?**
A: PostgreSQL. Configure credentials in `config.py`.

**Q: How do I reset the database?**
A: Drop tables manually in PostgreSQL, then rerun the app.

## File Import

**Q: What file formats are supported?**
A: CSV and TXT files with columns: index_number, full_name, course, score.

**Q: How do I import students from a file?**
A: Use CLI menu option 8 (GUI file loader).

## Reports

**Q: How are reports generated?**
A: TXT and PDF reports, sorted by name then grade, saved in project directory.

**Q: Can I customize report formats?**
A: Yes, modify `report_utils.py`.

## Errors & Logging

**Q: Where are errors logged?**
A: All errors are logged to `app.log`.

**Q: What if the log file is missing?**
A: Ensure write permissions in the project directory.

## Troubleshooting

**Q: DB connection fails. What should I check?**
A: Verify credentials in `config.py` and PostgreSQL service status.

**Q: GUI file loader does not open.**
A: Ensure Tkinter is installed and available.

**Q: File import fails.**
A: Check file format and data validity.

---

For more help, see `docs/USAGE_GUIDE.md` or open a GitHub issue.
