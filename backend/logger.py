# logger.py
# logging configuration and setup module

import logging  # import the logging module

def get_logger(name):  # define a function to get a logger by name
    logger = logging.getLogger(name)  # create or retrieve a logger instance
    logger.setLevel(logging.DEBUG)  # set the logging level to debug

    if not logger.handlers:  # check if the logger has no handlers
        file_handler = logging.FileHandler('app.log')  # create a file handler to write logs to 'app.log'
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')  # set the log message format
        file_handler.setFormatter(formatter)  # apply the formatter to the file handler
        logger.addHandler(file_handler)  # add the file handler to the logger

    return logger  # return the configured logger
