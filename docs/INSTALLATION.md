# Installation Guide

## Prerequisites
- Python 3.8+
- PostgreSQL database
- pip (Python package manager)

## Step-by-Step Installation

1. **Clone the repository**
   ```
   git clone <repo-url>
   cd students-result-management-tool
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Configure the database**
   - Edit `config.py` with your PostgreSQL credentials:
     ```python
     DB_NAME = "your_db_name"
     DB_USER = "your_db_user"
     DB_PASSWORD = "your_db_password"
     DB_HOST = "localhost"
     DB_PORT = "5432"
     ```

4. **Run the application**
   ```
   python main.py
   ```

## Platform Notes
- Windows, macOS, and Linux supported
- For GUI file loader, ensure Tkinter is installed (comes with most Python distributions)

## Troubleshooting
- If you encounter missing packages, re-run `pip install -r requirements.txt`
- For DB connection issues, verify credentials and PostgreSQL service status
- For GUI errors, ensure Tkinter is available

---

For advanced setup, see `docs/DB_SCHEMA.md` and `README.md`.
