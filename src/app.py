import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ctf_checkers.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db.init_app(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    import models
    db.create_all()
    logging.info("Database tables created")

    if not models.ServerState.query.filter_by(key='last_run_time').first():
        from datetime import datetime
        initial_state = models.ServerState(key='last_run_time', value=datetime.now().isoformat())
        db.session.add(initial_state)
        db.session.commit()
