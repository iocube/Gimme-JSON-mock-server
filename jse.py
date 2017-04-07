import urllib
import json


class JavaScriptExecuter(object):
    def __init__(self, code, context, modules=None, language='javascript'):
        self.code = code
        self.context = context
        self.language = language
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

    def run(self, host, port):
        request_params = urllib.request.Request(
            url='http://{host}:{port}/code'.format(host=host, port=port),
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
