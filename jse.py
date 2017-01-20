import urllib
import json

from settings import Settings


class Code(object):
    def __init__(self, code, context, modules):
        self.code = code
        self.context = context
        self.language = 'javascript'
        self.modules = modules if modules else []
        self.execution_result = None

    def serialize(self):
        return json.dumps(
            {
                'code': self.code,
                'context': self.context.serialize(),
                'language': self.language,
                'modules': self.modules
            }
        )

    def run(self):
        request_params = urllib.request.Request(
            url='http://{jse_host}:{jse_port}'.format(jse_host=Settings.JSE_HOST, jse_port=Settings.JSE_PORT),
            data=bytes(self.serialize(), encoding='utf-8'),
            method='POST',
            headers={'Content-type': 'application/json'}
        )

        f = urllib.request.urlopen(request_params)
        code_execution_result = ExecutionResult(json.loads(f.read().decode('utf-8')))
        f.close()

        self.execution_result = code_execution_result

        return code_execution_result


class ExecutionResult(object):
    def __init__(self, result):
        self.raw = result
        gimme = result['context']['gimme']
        self.status = gimme['response']['status'] if 'status' in gimme['response'] else 200
        self.response = gimme['response']['response'] if 'response' in gimme['response'] else {}
        self.storage = gimme['storage'].items()


class Context(object):
    def __init__(self, flask_request, flask_route_params, storage_list):
        self.query_params = self.__get_query_params_from_request(flask_request)
        self.method = flask_request.method
        self.path = flask_request.path
        self.full_path = flask_request.full_path
        self.payload = flask_request.get_json(silent=True) or {}
        self.route_params = flask_route_params
        self.storage = {storage['_id']: json.loads(storage['value']) for storage in storage_list}
        self.response = {}

    def serialize(self):
            print(self.storage)
            return {
                'gimme': {
                    'queryParams': self.query_params,
                    'method': self.method,
                    'path': self.path,
                    'fullPath': self.full_path,
                    'payload': self.payload,
                    'params': self.route_params,
                    'storage': self.storage,
                    'response': self.response
                }
            }

    def __get_query_params_from_request(self, request):
        query_params = {}
        for arg in request.args:
            query_params[arg] = request.args.getlist(arg)

        return query_params
