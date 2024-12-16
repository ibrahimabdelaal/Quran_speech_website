from flask import Flask
from .models import db  # Import your database instance
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__,static_url_path='/static')
    
    # Configuration 'sqlite:///G:\\zyad website\\quran.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///G:\\speech website\\sec_website\\quran.db"
    db.init_app(app)

    with app.app_context():
        db.create_all()  # Create database tables
    # Import and register routes
    migrate = Migrate(app, db)
    return app
