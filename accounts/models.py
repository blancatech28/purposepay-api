# accounts/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models



class CustomUserManager(BaseUserManager):
    """
    Manager for CustomUser model.
    Handles creating regular users and superusers.
    """
    def create_user(self, username, email, password=None, **extra_fields):
        """
        Create and save a regular user with given email and password.
        """
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Create and save a superuser with given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(username, email, password, **extra_fields)



class CustomUser(AbstractUser):
    """
    A custom User model for the PurposePay API, using email as the primary
    authentication identifier.
    """
    
    email = models.EmailField(unique=True, verbose_name='email address',help_text='Required for login and must be unique.'
    )
    
    # USERNAME_FIELD changed to 'email' so users log in with their email 
    # instead of a traditional username.
    USERNAME_FIELD = 'email'
    

    REQUIRED_FIELDS = ['username']  # Username is still required for other purposes.

    objects = CustomUserManager()     # Custom manager for user creation.


    # PurposePay Role Flags (Defining the User Type)
    is_vendor = models.BooleanField(
        default=False,
        help_text='Designates whether this user has a Vendor profile and can redeem vouchers.'
    )
    
    is_customer = models.BooleanField(
        default=True,
        help_text='Designates whether this user is a Customer/Sender and can create vouchers.'
    )


    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'



# Create your models here.
