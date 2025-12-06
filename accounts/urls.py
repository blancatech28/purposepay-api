from django.urls import path
from .views import RegisterView, LoginView, UserProfileView, LogoutView

# Namespace for the accounts app to avoid URL name clashes
app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'), # User registration endpoint
    path('login/', LoginView.as_view(), name='login'), # User login endpoint
    path('logout/', LogoutView.as_view(), name='logout'), # User logout endpoint
    path('me/', UserProfileView.as_view(), name='user-profile'), # User profile endpoint
]