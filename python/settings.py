with open('enviroment') as fin:
    env = {x[0]: x[1].strip() 
           for x in [line.split('=') for line in fin]}

DB_CONFIG = {
    'user': os.environ.get('RITTER_DB_USER'),
    'password': os.environ.get('RITTER_DB_PASSWORD'),
    'host': os.environ.get('RITTER_DB_HOST'),
    'database': 'Ritter'
}

COOKIEJAR_PATH = "python/.cookiejar"

PASSWORD_SALT = env['SALT']

PORT = 80
