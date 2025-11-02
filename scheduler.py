import logging
import time

import schedule
from dotenv import load_dotenv

from contacts_checker import check_all


def configure_logging():
    datefmt = '%d-%m %H:%M:%S'

    console_format = '[%(levelname)s] : %(message)s'
    file_format = '%(asctime)s [%(levelname)s] : %(message)s | %(name)s'

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    console_formatter = logging.Formatter(console_format, datefmt=datefmt)
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler('main-log.log', mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter(file_format, datefmt=datefmt)
    file_handler.setFormatter(file_formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler], force=True)

    for noisy in ['googleapiclient', 'PIL', 'requests', 'urllib3', 'asyncio', 'werkzeug', 'flask', 'schedule',
                  'peewee']:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(5)


if __name__ == "__main__":
    load_dotenv()
    configure_logging()
    logging.info("Starting scheduler...")
    schedule.every(30).seconds.do(check_all)
    scheduler_loop()
