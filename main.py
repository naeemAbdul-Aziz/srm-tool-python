# main.py
# main entry point for the student result management cli application


from db import create_tables, connect_to_db

def main():
    # step 1: connect to database and create tables
    try:
        print("\nConnecting to database...")
        conn = connect_to_db()
        print("Creating tables...")
        create_tables(conn=conn)
        print("Tables created successfully.")
    except Exception as e:
        print(f"error with database connection or table creation: {e}")
        return

    from menu import run_menu
    print("Launching Student Result Management CLI...")
    run_menu()

if __name__ == "__main__":
    main()
