from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.middleware import RemoteUserMiddleware

class AuthentikRemoteUserMiddleware(RemoteUserMiddleware):
    header = 'HTTP_X_AUTHENTIK_EMAIL'

    def process_request(self, request):
        email = request.META.get(self.header)
        if not email:
            email = request.META.get('HTTP_X_FORWARDED_EMAIL')
        
        if email:
            email = email.strip().lower()
            username = email.split('@')[0]
            first_name = request.META.get('HTTP_X_AUTHENTIK_NAME', '')
            
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': email,
                'first_name': first_name,
            })
            if not user.email and email:
                user.email = email
                user.save()

            if request.user != user:
                request.user = user
                login(request, user, backend='django.contrib.auth.backends.RemoteUserBackend')
