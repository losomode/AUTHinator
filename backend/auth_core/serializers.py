"""
Serializers for authentication and user management.
"""
from rest_framework import serializers
from users.models import User, Customer


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model."""
    
    class Meta:
        model = Customer
        fields = ['id', 'name', 'contact_email', 'is_active']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model (minimal auth data only).
    Services should query USERinator for company/role context.
    """
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'is_verified', 'is_active'
        ]
        read_only_fields = ['id', 'is_verified']


class LoginSerializer(serializers.Serializer):
    """Serializer for login requests."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration (no customer required).
    
    User profiles and company assignments are managed in USERinator.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role'
        ]
        extra_kwargs = {
            'email': {'validators': []},  # Disable default validators, we'll add custom validation
        }
    
    def validate_username(self, value):
        """Validate username is unique."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_email(self, value):
        """Validate email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate(self, attrs):
        """Validate password match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        
        # Prevent users from registering as admin
        role = attrs.get('role', User.USER)
        if role == User.ADMIN:
            attrs['role'] = User.USER
        
        return attrs
    
    def create(self, validated_data):
        """Create new user with unverified status (no customer assignment).
        
        Company assignment should be done in USERinator after admin approval.
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            is_verified=False,
            is_active=True,  # Active but not verified
            **validated_data
        )
        return user


class UserApprovalSerializer(serializers.Serializer):
    """Serializer for user approval."""
    pass  # No fields needed for approval


class UserRejectionSerializer(serializers.Serializer):
    """Serializer for user rejection."""
    reason = serializers.CharField(required=True, max_length=500)
