import json
import os
import flask
import pymongo
from flask import Response, request
from urllib.error import HTTPError
from string import Template

from settings import Settings
from decorators import crossdomain
from jse import Code
import storageDAO
import endpointDAO
import js_code

connection = pymongo.MongoClient(Settings.DATABASE_HOST, Settings.DATABASE_PORT)
database = connection[Settings.DATABASE_NAME]

application = flask.Flask(__name__)
application.config.from_object(Settings)

js_code_template = Template(js_code.code)

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
        endpoint = endpointDAO.find_one(endpoint_id)
        code = endpoint[request.method.lower()]
        storage_list = storageDAO.find_many(endpoint['storage'])
        query_params = {arg: request.args.getlist(arg) for arg in request.args}

        code_execution_context = {
            '$g': {
                'storage': {storage['_id']: json.loads(storage['value']) for storage in storage_list},
                'response': {
                    'status': 200,
                    'value': {}
                }
            }
        }

        code_to_execute = js_code_template.substitute(**{
            'query_params': query_params,
            'method': request.method,
            'path': request.path,
            'full_path': request.full_path,
            'payload': request.get_json(silent=True) or {},
            'params': kwargs,
            'code': code
        })

        try:
            code_instance = Code(code=code_to_execute, context=code_execution_context)
            execution_result = code_instance.run(Settings.JSE_HOST, Settings.JSE_PORT)
        except HTTPError as error:
            return Response(response=error.read().decode('utf-8'),
                            status=200,
                            mimetype='application/json')

        for storage_id, storage_value in execution_result.storage:
            storageDAO.save(storage_id, storage_value)

        return Response(response=json.dumps(execution_result.response),
                        status=execution_result.status,
                        mimetype='application/json')

    return endpoint_handler

# register all endpoints
all_endpoints = endpointDAO.find()

for each in all_endpoints:
    application.add_url_rule(
        rule=each['route'],
        endpoint=str(each['_id']),
        view_func=endpoint_handler_wrapper(each['_id']),
        methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    )
