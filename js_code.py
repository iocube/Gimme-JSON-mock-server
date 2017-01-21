# $g should be passed in context and extended here.
# $g.response and $g.storage context variables are not part of the template
# they are passed to JSE as a dictionary.

code = """
$$g.queryParams = $query_params;
$$g.method = "$method";
$$g.path = "$path";
$$g.fullPath = "$full_path";
$$g.payload = $payload;
$$g.params = $params;
$$g.set_response =  function(status, value) {
    $$g.response.status = status;
    $$g.response.value = value;
}

// your code here
$code
"""