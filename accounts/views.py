# accounts/views.py

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout, get_user_model

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, UpdateUserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """POST /account/register/ - create a new user"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(APIView):
    """POST /account/login/ - authenticate user and return token"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Explicit token creation (safe even if signals fail)
        token, _ = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user, context={"request": request}).data

        return Response({
            "token": token.key,
            "user": user_data,
            "message": f"Welcome back, {user.username}!"
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """POST /account/logout/ - delete user's token"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        logout(request)
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """GET /account/me/ - view profile, PUT/PATCH - update profile"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateUserSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Add dynamic welcome message to serializer context
        context["welcome_message"] = f"Welcome {self.request.user.username}!"
        return context
