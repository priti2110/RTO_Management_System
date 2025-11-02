import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://rtoprojectadmin:Mtech-proj@rto-project-db.postgres.database.azure.com:5432/postgresdb')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
