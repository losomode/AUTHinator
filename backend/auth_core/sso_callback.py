"""
SSO callback handling for AUTHinator.
After successful SSO login, create JWT token and redirect to frontend.
"""
from django.shortcuts import redirect
from django.views import View
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.models import SocialAccount
from users.models import User, Customer


class SSOCallbackView(View):
    """
    Handle SSO login callback.
    Creates or gets user, generates JWT tokens, and redirects to frontend with token.
    """
    
    def get(self, request):
        # User should be authenticated by allauth at this point
        if not request.user.is_authenticated:
            # If not authenticated, redirect to login
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3001')
            return redirect(f'{frontend_url}/login')
        
        user = request.user
        
        # Ensure user is verified and active (SSO users auto-verified)
        if not user.is_verified:
            user.is_verified = True
            user.save()
        
        # Generate minimal JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Get the 'next' parameter if it was passed through the login flow
        next_url = request.session.get('socialaccount_next_url', None)
        
        # Get frontend URL from settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3001')
        
        if next_url:
            # Redirect back to the service that initiated login
            return redirect(f'{next_url}?token={access_token}')
        else:
            # Redirect to frontend home with token
            return redirect(f'{frontend_url}/?token={access_token}')
