import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')

    # PostgreSQL
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', 5432)
    DB_NAME = os.environ.get('DB_NAME', 'projectx_db')

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

    # SendGrid
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
