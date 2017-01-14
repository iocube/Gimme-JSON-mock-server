import json
import os
import flask
import urllib
import pymongo
from flask import Response, request
from pymongo import ReturnDocument
from urllib.error import HTTPError

from settings import Settings
from decorators import crossdomain

connection = pymongo.MongoClient(Settings.DATABASE_HOST, Settings.DATABASE_PORT)
database = connection[Settings.DATABASE_NAME]

application = flask.Flask(__name__)
application.config.from_object(Settings)


def get_code_to_execute(endpoint):
    method = request.method.lower()
    return endpoint[method]


def find_endpoint_by_id(endpoint_id):
    return database.endpoints.find_one({'_id': endpoint_id})


def find_multiple_storages_by_ids(ids):
    return [
        storage for storage in database.storage.find(
            {
                '_id': {'$in': ids}
            }
        )
    ]


def save_to_storage(storage_id, new_value):
    database.storage.find_one_and_update(
        {'_id': storage_id},
        {'$set': {'value': json.dumps(new_value)}},
        return_document=ReturnDocument.AFTER
    )


@application.route('/server/', methods=['DELETE'])
def restart():
    """
    Flask does not have method to restart server manually, to do it we'll
    update mtime for one of modules and that will trigger restart.

    This will work only if flask development server running with use_reloader=True.

    Restart is needed if new endpoints were added to database.
    """
    os.utime(Settings.TOUCH_ME_TO_RELOAD, None)
    return Response(response=json.dumps({}),
                    status=200,
                    mimetype='application/json')


def endpoint_handler_wrapper(endpoint_id):
    @crossdomain(methods=['OPTIONS', 'GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
    def endpoint_handler(*args, **kwargs):
        print("{method} {path}".format(method=request.method, path=request.path))

        endpoint = find_endpoint_by_id(endpoint_id)
        code = get_code_to_execute(endpoint)
        storage_list = find_multiple_storages_by_ids(endpoint['storage'])

        query_params = {}
        for arg in request.args:
            query_params[arg] = request.args.getlist(arg)

        built_in_code = """
        function response(status, resp) {
            gimme.response = {"status": status, "response": resp};
        }

        """

        sandbox = {
            'code': built_in_code + code,
            'context': {
                'gimme': {
                    'payload': request.get_json(silent=True) or {},
                    'request': {
                        'queryParams': query_params,
                        'method': request.method,
                        'path': request.path,
                        'fullPath': request.full_path
                    },
                    'storage': {storage['_id']: json.loads(storage['value']) for storage in storage_list},
                    'response': {}
                }
            },
            'language': 'javascript',
            'modules': []
        }

        sandbox_json = json.dumps(sandbox)

        request_params = urllib.request.Request(
            url='http://{jse_host}:{jse_port}'.format(jse_host=Settings.JSE_HOST, jse_port=Settings.JSE_PORT),
            data=bytes(sandbox_json, encoding='utf-8'),
            method='POST',
            headers={'Content-type': 'application/json'}
        )

        try:
            f = urllib.request.urlopen(request_params)
            sandbox_response = json.loads(f.read().decode('utf-8'))
            f.close()
        except HTTPError as error:
            return Response(response=error.read().decode('utf-8'),
                            status=200,
                            mimetype='application/json')

        for storage_id, storage_value in sandbox_response['context']['gimme']['storage'].items():
            save_to_storage(storage_id, storage_value)

        return Response(response=json.dumps(sandbox_response['context']['gimme']['response']['response']),
                        status=sandbox_response['context']['gimme']['response']['status'],
                        mimetype='application/json')

    return endpoint_handler

if __name__ == '__main__':
    # register all endpoints
    all_endpoints = database.endpoints.find()

    for each in all_endpoints:
        application.add_url_rule(
            rule=each['route'],
            endpoint=str(each['_id']),
            view_func=endpoint_handler_wrapper(each['_id']),
            methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        )

    application.run(port=Settings.PORT)

