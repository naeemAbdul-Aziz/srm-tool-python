
# Student Result Management CLI Tool

A command-line tool for secure management of student results, grades, and user accounts.

## Project Structure

```
├── main.py           # Main entry point for the application
├── auth.py           # Authentication and user management
├── db.py             # Database connection and operations
├── utils.py          # Utility functions and helpers
├── menu.py           # CLI menu system and role-based access
├── file_handler.py   # File import/export functionality
├── logger.py         # Logging configuration
├── config.py         # Configuration settings
├── requirements.txt  # Python dependencies
├── students.csv      # Example student data file
└── README.md         # This file
```

## Key Features (Version 1)

- CLI-only operation (no GUI)
- Secure user authentication (admin/student)
- Passwords are securely hashed
- Student sign up restricted to valid index numbers in the database
- Role-based login and menu logic
- Error handling for database operations
- PostgreSQL database integration

## Installation & Setup

1. **Clone the repository**
2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
3. **Configure your database settings:**
   - Create a `.env` file with your PostgreSQL connection details (see `config.py` for required variables)
4. **Prepare your database:**
   - Ensure your database is running and accessible
   - Create required tables by running the app once (tables are auto-created if missing)
5. **Run the application:**
   ```
   python main.py
   ```

## Usage

- **Sign Up:**
  - Admins: Choose a username and password
  - Students: Enter your index number (must exist in student records) and choose a password
- **Login:**
  - Role-based login for admin and student
- **Menu:**
  - Access features based on your role

## Requirements

- Python 3.8+
- PostgreSQL database

## Next Steps

- Bulk import of student accounts
- Automated password assignment for students
- Admin tools for password reset and account management

---
For questions or contributions, please open an issue or submit a pull request.
- Required Python packages (see requirements.txt)

## Configuration

Create a `.env` file in the root directory with the following variables:

```
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your_secret_key
```
