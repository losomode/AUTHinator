"""
URL configuration for AUTHinator.

Routes:
    /admin/ - Django admin interface
    /api/auth/ - Authentication endpoints
    /api/users/ - User management endpoints
    /api/services/ - Service registry endpoints
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from auth_core.views import health_check, login, refresh_token, logout, me
from auth_core.admin_views import change_password, change_username, create_user, set_user_password, set_user_username, deactivate_user
from auth_core.sso_views import sso_providers
from auth_core.sso_callback import SSOCallbackView
from users.views import RegisterView, PendingUsersView, approve_user, reject_user
from services.views import ServiceViewSet
from mfa.views import (
    totp_status, totp_setup, totp_confirm, totp_disable,
    webauthn_credentials, webauthn_register_begin, webauthn_register_complete,
    webauthn_credential_delete,
    mfa_totp_verify, mfa_webauthn_begin, mfa_webauthn_complete,
)

# Router for service registry
router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')

urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication endpoints
    path('api/auth/health/', health_check, name='health-check'),
    path('api/auth/login/', login, name='login'),
    path('api/auth/refresh/', refresh_token, name='refresh'),
    path('api/auth/logout/', logout, name='logout'),
    path('api/auth/me/', me, name='me'),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/change-password/', change_password, name='change-password'),
    path('api/auth/change-username/', change_username, name='change-username'),
    path('api/auth/create-user/', create_user, name='create-user'),
    path('api/auth/admin/set-password/', set_user_password, name='set-user-password'),
    path('api/auth/admin/set-username/', set_user_username, name='set-user-username'),
    path('api/auth/admin/deactivate-user/', deactivate_user, name='deactivate-user'),
    path('api/auth/sso-providers/', sso_providers, name='sso-providers'),
    # TOTP (2FA) endpoints
    path('api/auth/totp/status/', totp_status, name='totp-status'),
    path('api/auth/totp/setup/', totp_setup, name='totp-setup'),
    path('api/auth/totp/confirm/', totp_confirm, name='totp-confirm'),
    path('api/auth/totp/disable/', totp_disable, name='totp-disable'),
    # WebAuthn endpoints
    path('api/auth/webauthn/credentials/', webauthn_credentials, name='webauthn-credentials'),
    path('api/auth/webauthn/register/begin/', webauthn_register_begin, name='webauthn-register-begin'),
    path('api/auth/webauthn/register/complete/', webauthn_register_complete, name='webauthn-register-complete'),
    path('api/auth/webauthn/credentials/<int:credential_id>/', webauthn_credential_delete, name='webauthn-credential-delete'),
    # MFA login verification endpoints
    path('api/auth/mfa/totp-verify/', mfa_totp_verify, name='mfa-totp-verify'),
    path('api/auth/mfa/webauthn-begin/', mfa_webauthn_begin, name='mfa-webauthn-begin'),
    path('api/auth/mfa/webauthn-complete/', mfa_webauthn_complete, name='mfa-webauthn-complete'),
    # User management endpoints (under /api/auth/users/ to avoid conflict with USERinator)
    path('api/auth/users/pending/', PendingUsersView.as_view(), name='pending-users'),
    path('api/auth/users/<int:pk>/approve/', approve_user, name='approve-user'),
    path('api/auth/users/<int:pk>/reject/', reject_user, name='reject-user'),
    # Service registry
    path('api/', include(router.urls)),
    # SSO callback after successful login
    path('accounts/profile/', SSOCallbackView.as_view(), name='sso-callback'),
    # Allauth URLs for SSO
    path('accounts/', include('allauth.urls')),
]
