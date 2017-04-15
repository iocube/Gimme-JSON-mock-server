import json
import os
from urllib.error import HTTPError

import flask
from flask import Response, request, views

import js_code
from dao import endpoint_dao, storage_dao
from decorators import crossdomain
from jse import JavaScriptExecuter
from settings import Settings

application = flask.Flask(__name__)
application.config.from_object(Settings)


class Server(views.MethodView):
    decorators = [
        crossdomain(methods=['OPTIONS', 'GET', 'DELETE'])
    ]

    def get(self):
        """
        Get server status.
        """

        return Response(
            response=json.dumps({"status": "ok"}),
            status=200,
            mimetype='application/json'
        )

    def delete(self):
        """
        Restart server.
        Flask does not have method to restart server manually, to do it we'll
        update mtime for one of modules and that will trigger restart.

        This will work only if flask development server running with use_reloader=True.

        Restart is needed if new endpoints were added to database.
        """
        os.utime(Settings.TOUCH_ME_TO_RELOAD, None)
        return Response(response=json.dumps({}),
                        status=200,
                        mimetype='application/json')


def generic_route_handler(endpoint_id):
    @crossdomain(methods=['OPTIONS', 'GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
    def wrapper(*args, **kwargs):
        endpoint = endpoint_dao.find_one(endpoint_id)

        storage_list = storage_dao.find_many(endpoint['storage'])
        ctx_var_storage = {storage['_id']: json.loads(storage['value']) for storage in storage_list}
        code_execution_context = js_code.create_context(storage=ctx_var_storage)

        # concatenate $g code and endpoint handler code
        code_to_execute = js_code.code_concat([
            js_code.prepare_g_object(flask_request=request, flask_router_args=kwargs),
            endpoint[request.method.lower()]
        ])

        try:
            jse_instance = JavaScriptExecuter(code=code_to_execute, context=code_execution_context)
            execution_result = jse_instance.run(Settings.JSE_HOST, Settings.JSE_PORT)
        except HTTPError as error:
            return Response(response=error.read().decode('utf-8'),
                            status=200,
                            mimetype='application/json')

        for storage_id, storage_value in execution_result.storage:
            storage_dao.save(storage_id, storage_value)

        return Response(response=json.dumps(execution_result.response),
                        status=execution_result.status,
                        mimetype='application/json')

    return wrapper

application.add_url_rule('/gimme-mock-server/', view_func=Server.as_view('server'))

# find all endpoints and register `generic_route_handler` as view_func for each of them
for each_endpoint in endpoint_dao.find():
    application.add_url_rule(
        rule=each_endpoint['route'],
        endpoint=str(each_endpoint['_id']),
        view_func=generic_route_handler(each_endpoint['_id']),
        methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    )
