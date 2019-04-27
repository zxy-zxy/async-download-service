import sys
import logging

FORMATTER = logging.Formatter('%(asctime)s — %(name)s — %(levelname)s — %(message)s')


def _get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_logger(logger_name, logging_lvl):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_lvl)
    logger.addHandler(_get_console_handler())
    logger.propagate = False
    return logger
