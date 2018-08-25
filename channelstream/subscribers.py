def handle_new_request(event):
    event.request.handle_cors()
    print(event.request.method, event.request.url)
