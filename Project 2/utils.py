import logging
import sys

INTERFACE = {"QUERY": 0, "DEPOSIT": 1, "WITHDRAW": 2}
INTERFACE_MAP = {0: "QUERY", 1: "DEPOSIT", 2: "WITHDRAW"}
RESPONSE_STATUS = {0: "SUCCESS", 1: "FAILURE", 2: "ERROR"}
RESPONSE_STATUS_MAP = {"SUCCESS": 0, "FAILURE": 1, "ERROR": 2}

"""
THis is a config using the python logging system
to configure for logging results.
"""
def config_logger(name: str):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[Process %(process)d %(asctime)s] %(message)s', "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger
'''
Performs the logging action.
'''
def log_data(logger: logging.Logger, message: str):
    logger.info(message)
    sys.stdout.flush()