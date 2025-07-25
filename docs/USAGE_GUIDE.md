# Usage Guide

## CLI Menu Options

1. **View all student records**
   - Lists all students in the database
2. **View student by index number**
   - Search for a student by their unique index number
3. **Update student score**
   - Update the score and grade for a student
4. **Export summary report to text file**
   - Generates a TXT summary report
5. **Export summary report to PDF**
   - Generates a PDF summary report
6. **Insert a new student manually**
   - Add a student record via CLI
7. **Analyze grade summary**
   - View grade distribution statistics
8. **Load students from file (GUI)**
   - Use a graphical file picker to import students from CSV/TXT
9. **Exit**
   - Quit the application

## File Import Format
- CSV/TXT: `index_number, full_name, course, score`
- Example:
  ```
  12345678, John Doe, CS101, 85
  ```

## Generating Reports
- TXT and PDF reports are saved in the project directory
- Reports are sorted by name, then grade

## GUI File Loader
- Option 8 opens a Tkinter window for file selection
- Select a valid CSV/TXT file to import student records

## Error Handling
- Errors are logged to `app.log`
- User-facing errors are printed in CLI/GUI

## Example Workflow
1. Start the app: `python main.py`
2. Choose option 6 to add a student
3. Choose option 4 or 5 to export a summary report
4. Use option 8 to import students from a file

---

For advanced usage, see `docs/DETAILED_DOC.md`.
