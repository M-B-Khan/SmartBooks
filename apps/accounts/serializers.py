from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import BusinessProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration with business profile creation."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    business_name = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password2', 'business_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        business_name = validated_data.pop('business_name')
        validated_data.pop('password2')

        # Create user
        user = User.objects.create_user(**validated_data)

        # Auto-create business profile
        BusinessProfile.objects.create(
            user=user,
            business_name=business_name,
            business_email=user.email,
        )

        return user


class UserSerializer(serializers.ModelSerializer):
    """Read serializer for user data."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'is_verified', 'date_joined']
        read_only_fields = ['id', 'is_verified', 'date_joined']


class BusinessProfileSerializer(serializers.ModelSerializer):
    """Serializer for business profile."""

    class Meta:
        model = BusinessProfile
        fields = [
            'id', 'business_name', 'business_email', 'phone',
            'address', 'city', 'country', 'currency', 'tax_number',
            'logo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs