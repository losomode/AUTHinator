"""
Client for communicating with USERinator service.

Fetches user role information (role_level, role_name) from USERinator
for inclusion in JWT token claims during login.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class UserinatorClient:
    """Client for querying USERinator API."""

    def __init__(self):
        self.api_url = settings.USERINATOR_API_URL
        self.service_key = settings.USERINATOR_SERVICE_KEY

    def get_user_role(self, user_id):
        """
        Fetch role_level and role_name for a user from USERinator.

        Uses X-Service-Key header for server-to-server auth (no JWT needed).

        Args:
            user_id: AUTHinator user ID (matches USERinator UserProfile.user_id)

        Returns:
            dict with role_name and role_level, or defaults if unavailable.
        """
        defaults = {"role_name": "UNKNOWN", "role_level": 0}

        try:
            response = requests.get(
                f"{self.api_url}{user_id}/role/",
                headers={"X-Service-Key": self.service_key},
                timeout=3,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "role_name": data.get("role_name", defaults["role_name"]),
                    "role_level": data.get("role_level", defaults["role_level"]),
                }

            if response.status_code == 404:
                # User has no USERinator profile yet — expected during migration
                logger.info(
                    "No USERinator profile for user %s (404)", user_id
                )
            else:
                logger.warning(
                    "USERinator role query failed for user %s: HTTP %s",
                    user_id,
                    response.status_code,
                )
        except requests.RequestException as exc:
            logger.warning("USERinator unreachable for user %s: %s", user_id, exc)

        return defaults


# Singleton instance
userinator_client = UserinatorClient()
