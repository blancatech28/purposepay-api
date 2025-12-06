# accounts/serializers.py
from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate



class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user (signup).
    Validates unique email and optional role flags.
    """
    password = serializers.CharField(write_only=True, min_length=6)
    username = serializers.CharField(required=True, max_length=15)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'is_vendor', 'is_customer']

    def validate_email(self, value):
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        if CustomUser.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value


    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for logging in a user using email and password.
    Checks invalid credentials and inactive accounts.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
            if not user.is_active:
                raise serializers.ValidationError("This account is inactive.")
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError("Email and password are required.")


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing user profile, including role flags.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'is_vendor', 'is_customer']




class UpdateUserSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile and role flags.
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'is_vendor', 'is_customer']
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate_email(self, value):
        user = self.instance
        if CustomUser.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        user = self.instance
        if CustomUser.objects.filter(username__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value


    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.is_vendor = validated_data.get('is_vendor', instance.is_vendor)
        instance.is_customer = validated_data.get('is_customer', instance.is_customer)
        instance.save()
        return instance