import json
from pymongo import ReturnDocument
from database import database


def find_many(ids):
    return [
        storage for storage in database.storage.find(
            {
                '_id': {'$in': ids}
            }
        )
    ]


def save(storage_id, new_value):
    database.storage.find_one_and_update(
        {'_id': storage_id},
        {'$set': {'value': json.dumps(new_value)}},
        return_document=ReturnDocument.AFTER
    )