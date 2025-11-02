import logging
import os

from dotenv import load_dotenv
from flask import Flask


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    from .auth import auth_bp
    from .dashboard import dashboard_bp
    from .api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)

    return app


def configure_logging():
    datefmt = '%d-%m %H:%M:%S'

    console_format = '[%(levelname)s] : %(message)s'
    file_format = '%(asctime)s [%(levelname)s] : %(message)s | %(name)s'

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    console_formatter = logging.Formatter(console_format, datefmt=datefmt)
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler('flask-main-log.log', mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter(file_format, datefmt=datefmt)
    file_handler.setFormatter(file_formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler], force=True)

    for noisy in ['googleapiclient', 'PIL', 'requests', 'urllib3', 'asyncio', 'werkzeug', 'flask', 'schedule',
                  'peewee']:
        logging.getLogger(noisy).setLevel(logging.WARNING)


configure_logging()
load_dotenv()
app = create_app()
