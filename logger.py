import logging
from logging.handlers import RotatingFileHandler
from tqdm import tqdm

class TqdmHandler(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        tqdm.write(msg)

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = RotatingFileHandler(
        'screenshot_crawler.log',
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = TqdmHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
