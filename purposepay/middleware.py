from django.shortcuts import redirect

class CaseInsensitiveMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        # If there are uppercase letters, redirect to the lowercase version
        if any(char.isupper() for char in path):
            return redirect(path.lower(), permanent=True)

        return self.get_response(request)
