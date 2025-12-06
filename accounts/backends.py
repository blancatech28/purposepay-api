# accounts/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Authenticate users using their email and password.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # login with email (username here is actually email)
        try:
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
    

    def get_user(self, user_id):
        """
        Get a user instance by user ID.
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None