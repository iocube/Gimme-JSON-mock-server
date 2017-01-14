import functools
from flask import request, current_app


def crossdomain(origin='*', methods=None, headers=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            default_options_response = current_app.make_default_options_response()

            if not methods:
                # NOTE: default_options_response might not have 'allow' header
                # for example, when there is an error handler on the application level (not on blueprint).
                allowed_methods = default_options_response.headers['allow'].split(', ')
            else:
                allowed_methods = ', '.join(sorted(method.upper() for method in methods))

            if not headers:
                allowed_headers = 'Accept, Accept-Language, Content-Language, Content-Type'
            else:
                allowed_headers = ', '.join(headers)

            crossdomain_headers = {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': allowed_methods,
                'Access-Control-Allow-Headers': allowed_headers
            }

            if request.method == 'OPTIONS':
                default_options_response.headers.extend(crossdomain_headers)
                return default_options_response

            # NOTE: func might raise an exception (i.e BadRequest), currently this error is not catched so
            # execution stops here before headers are set for CORS.
            crossdomain_response = func(*args, **kwargs)
            crossdomain_response.headers.extend(crossdomain_headers)

            return crossdomain_response

        # tell flask that OPTIONS requests will be handled manually by the decorator.
        wrapper.required_methods = ['OPTIONS']
        wrapper.provide_automatic_options = False
        return wrapper
    return decorator

