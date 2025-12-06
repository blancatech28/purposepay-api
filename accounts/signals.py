# accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def create_auth_token(sender, instance, created, **kwargs):
    """
    Automatically create an auth token when a new user signs up.
    """
    if created:
        Token.objects.create(user=instance)
