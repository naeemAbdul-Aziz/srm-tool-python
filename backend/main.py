# main.py
# main entry point for the student result management cli application

from db import create_tables, connect_to_db
from fastapi import FastAPI, HTTPException, UploadFile, File
from logger import get_logger

logger = get_logger(__name__)

def main():
    # step 1: connect to database and create tables
    try:
        logger.info("Connecting to database...")
        conn = connect_to_db()
        logger.info("Creating tables...")
        create_tables(conn=conn)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error with database connection or table creation: {e}", exc_info=True)
        return

    from menu import run_menu
    logger.info("Launching Student Result Management CLI...")
    try:
        run_menu()
    except Exception as e:
        logger.error(f"Error running menu: {e}", exc_info=True)

if __name__ == "__main__":
    import uvicorn
    try:
        logger.info("Starting FastAPI server with Uvicorn...")
        uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
    except Exception as e:
        logger.error(f"Error starting Uvicorn server: {e}", exc_info=True)
