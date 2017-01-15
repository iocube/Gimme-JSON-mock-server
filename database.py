import pymongo
from settings import Settings


connection = pymongo.MongoClient(Settings.DATABASE_HOST, Settings.DATABASE_PORT)
database = connection[Settings.DATABASE_NAME]
