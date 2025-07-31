# main.py - main entry point for the student result management cli application

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

    from menu import main_menu_loop
    logger.info("launching student result management cli...")
    try:
        main_menu_loop()
    except Exception as e:
        logger.error(f"error running menu: {e}", exc_info=True)

if __name__ == "__main__":
    main() 
    # import uvicorn
    # try:
    #     logger.info("starting fastapi server with uvicorn...")
    #     uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
    # except Exception as e:
    #     logger.error(f"error starting uvicorn server: {e}", exc_info=True)