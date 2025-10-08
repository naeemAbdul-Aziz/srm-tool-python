# main.py - main entry point for the student result management cli application

try:
    from .db import create_tables_if_not_exist, connect_to_db
except ImportError:
    from db import create_tables_if_not_exist, connect_to_db
from fastapi import FastAPI, HTTPException, UploadFile, File
from logger import get_logger

logger = get_logger(__name__)

def main():
    # step 1: connect to database and create tables
    try:
        logger.info("connecting to database...")
        conn = connect_to_db()
        if conn:
            create_tables_if_not_exist(conn)
            conn.close()
            logger.info("tables created successfully.")
        else:
            logger.error("failed to connect to database")
            return
    except Exception as e:
        logger.error(f"error with database connection or table creation: {e}", exc_info=True)
        return

    try:
        from .menu import main_menu_loop
    except ImportError:
        from menu import main_menu_loop
    logger.info("launching student result management cli...")
    try:
        main_menu_loop()
    except Exception as e:
        logger.error(f"error running menu: {e}", exc_info=True)

if __name__ == "__main__":
    # main()  # CLI still available if desired
    import uvicorn, os, sys
    try:
        # Detect if we are in the project root (contains 'backend' dir) or already inside backend.
        cwd = os.getcwd()
        backend_dir = os.path.basename(cwd).lower() == 'backend'
        if backend_dir:
            # Ensure parent directory is on sys.path so 'backend' package can be resolved
            parent = os.path.dirname(cwd)
            if parent and parent not in sys.path:
                sys.path.insert(0, parent)
            target = "backend.api:app"  # We injected parent, so package import should now work
        else:
            target = "backend.api:app"

        logger.info(f"starting fastapi server with uvicorn (target={target})...")
        uvicorn.run(target, host="127.0.0.1", port=8000, reload=True)
    except Exception as e:
        logger.error(f"error starting uvicorn server: {e}", exc_info=True)