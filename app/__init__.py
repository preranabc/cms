from flask import Flask
from config import Config
import logging
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s %(name)s : %(message)s',
        handlers=[
            logging.StreamHandler(),                          # console
            logging.FileHandler('cms_app.log', encoding='utf-8')  # file
        ]
    )
    app.logger.setLevel(log_level)

    # ── Blueprints ────────────────────────────────────────────────────────────
    from app.views import main
    app.register_blueprint(main)

    with app.app_context():
        from app.models import init_db
        init_db()

    return app
