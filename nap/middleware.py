class BaseMiddleware:
    def handle_request(self, request):
        return request

    def handle_response(self, request, response):
        return response
