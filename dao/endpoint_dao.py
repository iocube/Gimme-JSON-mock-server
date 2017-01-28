from database import database


def find():
    return database.endpoints.find()


def find_one(endpoint_id):
    return database.endpoints.find_one({'_id': endpoint_id})
