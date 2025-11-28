from django.shortcuts import redirect
from django.urls import reverse

class PasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.user.is_authenticated and
            not request.user.is_superuser and
            request.user.profile.must_change_password and
            request.path != reverse('change_password')):
            
            return redirect('change_password')

        response = self.get_response(request)
        return response