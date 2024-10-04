import os
from . import settings

db_address = os.getenv('TESTING_TEMPLATE_DB_ADDRESS')
db_user = os.getenv('TESTING_TEMPLATE_DB_USER')
db_password = os.getenv('TESTING_TEMPLATE_DB_PASSWORD')
db_name = os.getenv('TESTING_TEMPLATE_DB_NAME')

tg_secret_token = os.getenv('TESTING_TEMPLATE_TG_TOKEN')

s3_access_key = os.getenv('TESTING_TEMPLATE_S3_ACCESS_KEY')
s3_secret_key = os.getenv('TESTING_TEMPLATE_S3_SECRET_KEY')

PASSWORD_ENCODING_SECRET = os.environ['TESTING_TEMPLATE_PASS_ENCODING_SECRET']
# to get a string like this run:
# openssl rand -hex 32


if settings.IS_PROD and None in (db_address, db_name, db_user, db_password):
    raise ValueError("Database connection env is not set")
