from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from app.commands import register_commands
from app.models import db
from config import Config
from app.bar.app import bar_bp
from app.user.login import login_bp
from app.user.register import register_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    migrate = Migrate()
    jwt = JWTManager()
    
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "OPTIONS", "DELETE", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": True
        }
    })
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    register_commands(app)
    
    with app.app_context():
        app.register_blueprint(bar_bp)
        app.register_blueprint(login_bp)
        app.register_blueprint(register_bp)
    
    return app
    