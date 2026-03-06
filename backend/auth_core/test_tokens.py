"""
Tests for JWT token enrichment with USERinator role claims.

Tests:
- create_enriched_tokens() adds role_level and role_name to access token
- Fallback when USERinator is unreachable
- Fallback when user has no USERinator profile (404)
- Login endpoint returns enriched tokens
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import Client
from rest_framework_simplejwt.tokens import AccessToken
from users.models import Customer, User
from auth_core.tokens import create_enriched_tokens
from auth_core.userinator_client import UserinatorClient


@pytest.mark.django_db
class TestCreateEnrichedTokens:
    """Test create_enriched_tokens helper."""

    @pytest.fixture
    def user(self):
        customer = Customer.objects.create(name="Test Corp", contact_email="t@t.com")
        user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            customer=customer,
            role=User.ADMIN,
        )
        user.is_verified = True
        user.save()
        return user

    @patch("auth_core.tokens.userinator_client")
    def test_enriched_tokens_include_role_claims(self, mock_client, user):
        """Tokens should include role_level and role_name from USERinator."""
        mock_client.get_user_role.return_value = {
            "role_name": "ADMIN",
            "role_level": 100,
        }

        tokens = create_enriched_tokens(user)

        assert "access" in tokens
        assert "refresh" in tokens

        # Decode the access token and check custom claims
        access = AccessToken(tokens["access"])
        assert access["role_level"] == 100
        assert access["role_name"] == "ADMIN"

    @patch("auth_core.tokens.userinator_client")
    def test_enriched_tokens_fallback_on_failure(self, mock_client, user):
        """Tokens should fall back to defaults when USERinator is unavailable."""
        mock_client.get_user_role.return_value = {
            "role_name": "UNKNOWN",
            "role_level": 0,
        }

        tokens = create_enriched_tokens(user)

        access = AccessToken(tokens["access"])
        assert access["role_level"] == 0
        assert access["role_name"] == "UNKNOWN"

    @patch("auth_core.tokens.userinator_client")
    def test_enriched_tokens_member_role(self, mock_client, user):
        """Tokens should include MEMBER role correctly."""
        mock_client.get_user_role.return_value = {
            "role_name": "MEMBER",
            "role_level": 10,
        }

        tokens = create_enriched_tokens(user)

        access = AccessToken(tokens["access"])
        assert access["role_level"] == 10
        assert access["role_name"] == "MEMBER"


@pytest.mark.django_db
class TestUserinatorClient:
    """Test UserinatorClient.get_user_role."""

    @patch("auth_core.userinator_client.requests.get")
    def test_successful_role_fetch(self, mock_get):
        """Should return role data from USERinator."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "role_name": "MANAGER",
            "role_level": 30,
        }
        mock_get.return_value = mock_response

        client = UserinatorClient()
        result = client.get_user_role(42)

        assert result["role_name"] == "MANAGER"
        assert result["role_level"] == 30
        mock_get.assert_called_once()
        # Verify service key header is sent
        call_kwargs = mock_get.call_args
        assert "X-Service-Key" in call_kwargs.kwargs.get("headers", call_kwargs[1].get("headers", {}))

    @patch("auth_core.userinator_client.requests.get")
    def test_user_not_found_returns_defaults(self, mock_get):
        """Should return defaults when user has no USERinator profile."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = UserinatorClient()
        result = client.get_user_role(999)

        assert result["role_name"] == "UNKNOWN"
        assert result["role_level"] == 0

    @patch("auth_core.userinator_client.requests.get")
    def test_connection_error_returns_defaults(self, mock_get):
        """Should return defaults when USERinator is unreachable."""
        import requests as req

        mock_get.side_effect = req.ConnectionError("refused")

        client = UserinatorClient()
        result = client.get_user_role(42)

        assert result["role_name"] == "UNKNOWN"
        assert result["role_level"] == 0

    @patch("auth_core.userinator_client.requests.get")
    def test_timeout_returns_defaults(self, mock_get):
        """Should return defaults when USERinator times out."""
        import requests as req

        mock_get.side_effect = req.Timeout("timeout")

        client = UserinatorClient()
        result = client.get_user_role(42)

        assert result["role_name"] == "UNKNOWN"
        assert result["role_level"] == 0

    @patch("auth_core.userinator_client.requests.get")
    def test_server_error_returns_defaults(self, mock_get):
        """Should return defaults on 500 response."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        client = UserinatorClient()
        result = client.get_user_role(42)

        assert result["role_name"] == "UNKNOWN"
        assert result["role_level"] == 0


@pytest.mark.django_db
class TestLoginReturnsEnrichedTokens:
    """Integration test: login endpoint returns tokens with role claims."""

    @pytest.fixture
    def user(self):
        customer = Customer.objects.create(name="Test Corp", contact_email="t@t.com")
        user = User.objects.create_user(
            username="loginuser",
            email="login@test.com",
            password="testpass123",
            customer=customer,
            role=User.ADMIN,
        )
        user.is_verified = True
        user.save()
        return user

    @patch("auth_core.tokens.userinator_client")
    def test_login_tokens_contain_role_claims(self, mock_client, user):
        """Login should return JWT with role_level and role_name claims."""
        mock_client.get_user_role.return_value = {
            "role_name": "ADMIN",
            "role_level": 100,
        }

        client = Client()
        response = client.post(
            "/api/auth/login/",
            {"username": "loginuser", "password": "testpass123"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data

        # Decode and verify claims
        access = AccessToken(data["access"])
        assert access["role_level"] == 100
        assert access["role_name"] == "ADMIN"
