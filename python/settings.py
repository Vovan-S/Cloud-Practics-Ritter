import os

DB_CONFIG = {
    'user': os.environ.get('RITTER_DB_USER'),
    'password': os.environ.get('RITTER_DB_PASSWORD'),
    'host': os.environ.get('RITTER_DB_HOST'),
    'database': 'Ritter'
}

COOKIEJAR_PATH = "python/.cookiejar"

PASSWORD_SALT = "supersecretpa$$wordsalt"

PORT = 80
