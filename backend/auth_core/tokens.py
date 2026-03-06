"""
Token utilities for AUTHinator.

Provides create_enriched_tokens() which adds role_level and role_name
custom claims to JWT access tokens by querying USERinator.
"""
from rest_framework_simplejwt.tokens import RefreshToken

from auth_core.userinator_client import userinator_client


def create_enriched_tokens(user):
    """
    Create JWT access + refresh tokens enriched with USERinator role claims.

    Queries USERinator /api/users/{id}/role/ for role_level and role_name,
    then injects them as custom claims in the access token.
    Falls back to role_level=0, role_name='UNKNOWN' if USERinator is
    unreachable or the user has no profile there.

    Args:
        user: AUTHinator User model instance

    Returns:
        dict with 'access' and 'refresh' token strings
    """
    role_info = userinator_client.get_user_role(user.id)

    refresh = RefreshToken.for_user(user)

    # Capture the access token once (it's a property that creates a new
    # instance each call), then inject custom claims.
    access = refresh.access_token
    access["role_level"] = role_info["role_level"]
    access["role_name"] = role_info["role_name"]

    return {
        "access": str(access),
        "refresh": str(refresh),
    }
