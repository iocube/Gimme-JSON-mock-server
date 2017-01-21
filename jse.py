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
                'context': self.context,
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
        context = result['context']['$g']
        self.status = context['response']['status'] if 'status' in context['response'] else 200
        self.response = context['response']['value'] if 'value' in context['response'] else {}
        self.storage = context['storage'].items()
