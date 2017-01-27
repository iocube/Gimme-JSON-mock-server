import os


class Settings(object):
    DATABASE_NAME = 'gimmejsondb'
    DATABASE_HOST = os.environ.get('GIMMEJSON_DATABASE_HOST', 'localhost')
    DATABASE_PORT = int(os.environ.get('GIMMEJSON_DATABASE_PORT', 27017))
    TOUCH_ME_TO_RELOAD = 'settings.py'
    JSE_HOST = 'localhost'
    JSE_PORT = 8000