# import os
# BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# class Config:
#     SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-in-production'
#     SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:Password@localhost:5433/learning_tracker"
#     # SQLALCHEMY_DATABASE_URI = (os.environ.get('DATABASE_URL') or
#     #     'sqlite:///' + os.path.join(BASE_DIR, 'learning_tracker.db'))
#     # SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:Password@localhost:5432/learning_tracker"
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'pdfs')
#     MAX_CONTENT_LENGTH = 16 * 1024 * 1024
#     ALLOWED_EXTENSIONS = {'pdf'}




import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-in-production'

    DATABASE_URL = os.environ.get('DATABASE_URL')

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'db.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'pdfs')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf'}