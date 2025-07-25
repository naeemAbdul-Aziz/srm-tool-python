# Database Schema Documentation

## Tables

### student_results
- **id**: SERIAL PRIMARY KEY
- **index_number**: VARCHAR(10) NOT NULL UNIQUE
- **full_name**: TEXT NOT NULL
- **course**: TEXT NOT NULL
- **score**: INTEGER NOT NULL CHECK (score >= 0 AND score <= 100)
- **grade**: CHAR(1)

### users
- **id**: SERIAL PRIMARY KEY
- **username**: TEXT UNIQUE NOT NULL
- **password**: TEXT NOT NULL

## Relationships
- No foreign keys; all tables are independent.

## Migration Notes
- Table creation is handled automatically in `db.py` via `create_tables()`.
- On first run, tables are created if they do not exist.
- To reset tables, drop them manually in PostgreSQL and rerun the app.

## Example SQL
```
CREATE TABLE IF NOT EXISTS student_results (
    id SERIAL PRIMARY KEY,
    index_number VARCHAR(10) NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    course TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    grade CHAR(1)
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
```

## Data Types
- SERIAL: Auto-increment integer
- VARCHAR(10): String, max 10 chars
- TEXT: String, unlimited length
- INTEGER: Whole number
- CHAR(1): Single character

## Indexes
- `index_number` in `student_results` is UNIQUE for fast lookup and updates.
- `username` in `users` is UNIQUE for authentication.

## Notes
- All inserts/updates use ON CONFLICT for upsert logic.
- All DB-modifying operations use rollback on error.
