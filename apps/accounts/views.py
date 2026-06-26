from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from .models import BusinessProfile, EmailVerificationToken
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    BusinessProfileSerializer,
    ChangePasswordSerializer,
)
from .tasks import send_verification_email

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    POST /api/accounts/register/
    Register a new user and auto-create their business profile.
    Returns JWT tokens immediately after registration.
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate email verification token
        token = get_random_string(64)
        EmailVerificationToken.objects.create(user=user, token=token)

        # Send verification email (background task)
        send_verification_email(user.id, token)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Registration successful. Please verify your email.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    """
    GET /api/accounts/verify-email/?token=<token>
    Verifies the user's email address.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = request.query_params.get('token')

        if not token:
            return Response(
                {'error': 'Token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            verification = EmailVerificationToken.objects.get(token=token, is_used=False)
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if verification.is_expired():
            return Response(
                {'error': 'Token has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark user as verified
        verification.user.is_verified = True
        verification.user.save(update_fields=['is_verified'])
        verification.is_used = True
        verification.save(update_fields=['is_used'])

        return Response({'message': 'Email verified successfully.'})


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/accounts/profile/  → Get current user profile
    PUT  /api/accounts/profile/  → Update current user profile
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class BusinessProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/accounts/business/  → Get business profile
    PUT  /api/accounts/business/  → Update business profile
    """

    serializer_class = BusinessProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.business_profile


class ChangePasswordView(APIView):
    """
    POST /api/accounts/change-password/
    Allows authenticated users to change their password.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Old password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        return Response({'message': 'Password changed successfully.'})


class LogoutView(APIView):
    """
    POST /api/accounts/logout/
    Blacklists the refresh token to log the user out.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except Exception:
            return Response(
                {'error': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST
            )