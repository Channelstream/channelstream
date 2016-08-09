def handle_cors(request):
    request.response.headers.add('Access-Control-Allow-Origin', '*')
    request.response.headers.add('XDomainRequestAllowed', '1')
    request.response.headers.add('Access-Control-Allow-Methods',
                                 'GET, POST, OPTIONS, PUT')
    request.response.headers.add('Access-Control-Allow-Headers',
                                 'Content-Type, Depth, User-Agent, '
                                 'X-File-Size, X-Requested-With, '
                                 'If-Modified-Since, X-File-Name, '
                                 'Cache-Control, Pragma, Origin, '
                                 'Connection, Referer, Cookie')
    request.response.headers.add('Access-Control-Max-Age', '86400')
