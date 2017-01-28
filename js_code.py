"""
    $g is an object that is available when user code is run on JSE server, it contains information
    such as http method, query params, payload (i.e if its POST) and etc for *current* request being made.

    With this information user has the choice to decide how to handle incoming request.

    NOTE: `$g.storage` and `$g.response` injected when instance of `JavaScriptExecuter` is created.
"""

from string import Template


g_object_template = Template("""
$$g.queryParams = $query_params;
$$g.method = "$method";
$$g.path = "$path";
$$g.fullPath = "$full_path";
$$g.payload = $payload;
$$g.params = $params;

$$g.setResponse = function(status, value) {
    $$g.response.status = status;
    $$g.response.value = value;
}


""")


def embed_code(g_object, code):
    return g_object + code


def prepare_g_object(flask_request, flask_router_args):
    args = {
        'query_params': {arg: flask_request.args.getlist(arg) for arg in flask_request.args},
        'method': flask_request.method,
        'path': flask_request.path,
        'full_path': flask_request.full_path,
        'payload': flask_request.get_json(silent=True) or {},
        'params': flask_router_args,
    }

    return g_object_template.substitute(args)


def create_context(storage):
    return {
            '$g': {
                'storage': storage,
                'response': {
                    'status': 200,
                    'value': {}
                }
            }
        }


def code_concat(to_concat):
    concatenated = ''
    for code in to_concat:
        concatenated += code
    return concatenated
