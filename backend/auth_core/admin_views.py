"""
Admin and self-service views for AUTHinator.

Endpoints:
- POST /api/auth/change-password/   — any authenticated user changes own password
- POST /api/auth/change-username/   — any authenticated user changes own username
- POST /api/auth/create-user/       — admin or service key creates a verified user
- POST /api/auth/admin/set-password/ — admin force-sets any user's password
"""
import logging
import secrets
import string

from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import User
from users.permissions import IsAdmin

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)


class ChangeUsernameSerializer(serializers.Serializer):
    new_username = serializers.CharField(required=True, min_length=3, max_length=150)
    password = serializers.CharField(required=True, write_only=True)

    def validate_new_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value


class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True, min_length=3, max_length=150)
    role = serializers.ChoiceField(choices=[User.ADMIN, User.USER], default=User.USER)
    temp_password = serializers.CharField(required=False, allow_blank=True, min_length=8)

    def validate_username(self, value):
        # Only block active users — inactive accounts can be reactivated
        if User.objects.filter(username=value, is_active=True).exists():
            raise serializers.ValidationError(
                "An active user with this username already exists."
            )
        return value

    def validate_email(self, value):
        # Only block active users — inactive accounts can be reactivated
        if User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError(
                "An active user with this email already exists."
            )
        return value


class SetUserPasswordSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_service_key_valid(request):
    key = request.META.get("HTTP_X_SERVICE_KEY", "")
    expected = getattr(settings, "SERVICE_REGISTRATION_KEY", "")
    return bool(key and expected and key == expected)


def _generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$"
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change own password. Requires current password for verification."""
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(
        request,
        username=request.user.username,
        password=serializer.validated_data["current_password"],
    )
    if user is None:
        return Response(
            {"detail": "Current password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(serializer.validated_data["new_password"])
    user.save()
    logger.info("User %s changed their own password.", user.username)
    return Response({"detail": "Password updated successfully."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_username(request):
    """Change own username. Requires current password for security."""
    serializer = ChangeUsernameSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(
        request,
        username=request.user.username,
        password=serializer.validated_data["password"],
    )
    if user is None:
        return Response(
            {"detail": "Password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_username = user.username
    user.username = serializer.validated_data["new_username"]
    user.save()
    logger.info("User %s renamed to %s.", old_username, user.username)
    return Response({"detail": "Username updated successfully.", "username": user.username})


@api_view(["POST"])
@permission_classes([AllowAny])  # Auth is checked manually below (JWT admin OR X-Service-Key)
def create_user(request):
    """Create a verified user account.

    Accessible to:
    - Admin users (role == ADMIN via JWT)
    - Internal services using X-Service-Key header (e.g. USERinator invitation approval)
    """
    is_admin = request.user and request.user.is_authenticated and request.user.is_admin()
    if not is_admin and not _is_service_key_valid(request):
        return Response(
            {"detail": "Authentication required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = CreateUserSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    temp_password = data.get("temp_password") or _generate_temp_password()

    # Reactivate if an inactive account already exists with this username
    existing = User.objects.filter(
        username=data["username"], is_active=False
    ).first() or User.objects.filter(
        email=data["email"], is_active=False
    ).first()

    if existing:
        existing.username = data["username"]
        existing.email = data["email"]
        existing.role = data.get("role", User.USER)
        existing.is_active = True
        existing.is_verified = True
        existing.rejection_reason = None
        existing.set_password(temp_password)
        existing.save()
        user = existing
        logger.info("Reactivated user %s (id=%s) via create_user endpoint.", user.username, user.id)
    else:
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=temp_password,
            role=data.get("role", User.USER),
            is_verified=True,
            is_active=True,
        )
        logger.info("Created user %s (id=%s) via create_user endpoint.", user.username, user.id)

    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "temp_password": temp_password,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])  # Auth checked manually (JWT admin OR X-Service-Key)
def deactivate_user(request):
    """Deactivate a user account so they can no longer log in.

    Accessible to admin users (JWT) or internal services (X-Service-Key).
    Sets is_active=False which immediately invalidates their JWT tokens.
    """
    is_admin = request.user and request.user.is_authenticated and request.user.is_admin()
    if not is_admin and not _is_service_key_valid(request):
        return Response({"detail": "Authentication required."}, status=status.HTTP_403_FORBIDDEN)

    user_id = request.data.get("user_id")
    if not user_id:
        return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    user.is_active = False
    user.save(update_fields=["is_active"])
    logger.info("Deactivated user %s (id=%s).", user.username, user.id)
    return Response({"detail": f"{user.username} deactivated. They can no longer log in."})


@api_view(["POST"])
@permission_classes([AllowAny])  # Auth checked manually (JWT admin OR X-Service-Key)
def set_user_password(request):
    """Force-set any user's password. Accessible to admin JWT or service key."""
    is_admin = request.user and request.user.is_authenticated and request.user.is_admin()
    if not is_admin and not _is_service_key_valid(request):
        return Response({"detail": "Authentication required."}, status=status.HTTP_403_FORBIDDEN)

    serializer = SetUserPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(pk=serializer.validated_data["user_id"])
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    user.set_password(serializer.validated_data["new_password"])
    user.save()
    logger.info("Password reset for user %s (id=%s).", user.username, user.id)
    return Response({"detail": f"Password for {user.username} updated successfully."})


class SetUsernameSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    new_username = serializers.CharField(required=True, min_length=3, max_length=150)

    def validate_new_username(self, value):
        if User.objects.filter(username=value, is_active=True).exists():
            raise serializers.ValidationError("An active user with this username already exists.")
        return value


@api_view(["POST"])
@permission_classes([AllowAny])  # Auth checked manually (JWT admin OR X-Service-Key)
def set_user_username(request):
    """Force-set any user's username. Accessible to admin JWT or service key."""
    is_admin = request.user and request.user.is_authenticated and request.user.is_admin()
    if not is_admin and not _is_service_key_valid(request):
        return Response({"detail": "Authentication required."}, status=status.HTTP_403_FORBIDDEN)

    serializer = SetUsernameSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(pk=serializer.validated_data["user_id"])
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    old_username = user.username
    user.username = serializer.validated_data["new_username"]
    user.save()
    logger.info("Username changed %s -> %s (id=%s).", old_username, user.username, user.id)
    return Response({"username": user.username, "detail": f"Username updated to {user.username}."})
