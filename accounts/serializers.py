# accounts/serializers.py
from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
import re

User = get_user_model()



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
    

    # Extra validation to ensure at least one role is selected and not both simultaneously
    def validate(self,data):
        is_vendor = data.get('is_vendor', False)
        is_customer = data.get('is_customer', False)
        if not is_vendor and not is_customer:
            raise serializers.ValidationError("At least one role (vendor or customer) must be selected.")
    

        if is_vendor and is_customer:
            raise serializers.ValidationError(
                "You cannot be both a vendor and a customer."
        )

        return data


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
        fields = [
            'id', 'username', 'email', 'is_customer',
            'is_vendor','phone_number', 'profile_pic'
            ]
        read_only_fields = fields




class UpdateUserSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile info.
    Role flags (is_vendor, is_customer) are excluded from updates to avoid security risks.
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'profile_pic']
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
    
    # Phone number validation for Ghanaian format
    def validate_phone_number(self, value):
        pattern = r"^(?:\+233|0)\d{9}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number must be in Ghanaian format."
            )
        
        # Check if phone number is used by another vendor
        if User.objects.filter(phone_number=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This phone number is already in use by another user.")
    
        return value 
    
    
    MAX_IMAGE_SIZE = 5 * 1024 * 1024 # 5MB

    def validate_profile_pic(self, value):
        allowed = ('.jpg', '.jpeg', '.png')
        if not value.name.lower().endswith(allowed):
            raise serializers.ValidationError("Profile picture must be JPG or PNG.")
        if value.size > self.MAX_IMAGE_SIZE:
            raise serializers.ValidationError("Image too large (max 5MB).")
        return value



    # Update instance
    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.profile_pic = validated_data.get('profile_pic', instance.profile_pic)
        instance.save()
        return instance