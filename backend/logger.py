# logger.py
# logging configuration and setup module

import logging  # import the logging module
import colorlog  # for color-coded logging

def get_logger(name):  # define a function to get a logger by name
    logger = logging.getLogger(name)  # create or retrieve a logger instance
    logger.setLevel(logging.DEBUG)  # set the logging level to debug

    if not logger.handlers:  # check if the logger has no handlers
        # file handler for writing logs to app.log
        file_handler = logging.FileHandler('app.log')  # create a file handler to write logs to 'app.log'
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')  # set the log message format
        file_handler.setFormatter(file_formatter)  # apply the formatter to the file handler
        logger.addHandler(file_handler)  # add the file handler to the logger

        # stream handler for color-coded console output
        stream_handler = logging.StreamHandler()
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
        stream_handler.setFormatter(color_formatter)
        logger.addHandler(stream_handler)

    return logger  # return the configured logger