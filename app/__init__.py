import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config


db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to continue.'
    login_manager.login_message_category = 'info'

    from app.routes.auth       import auth_bp
    from app.routes.dashboard  import dashboard_bp
    from app.routes.subjects   import subjects_bp
    from app.routes.topics     import topics_bp
    from app.routes.subtopics  import subtopics_bp
    from app.routes.mocks      import mocks_bp
    from app.routes.search     import search_bp
    from app.chatbot.routes    import chatbot_bp
    from app.routes.admin      import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(topics_bp)
    app.register_blueprint(subtopics_bp)
    app.register_blueprint(mocks_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(chatbot_bp)  
    app.register_blueprint(admin_bp)

    from app.admin import init_admin
    init_admin(app)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    with app.app_context():
        from app import models  # noqa
        db.create_all()

    return app