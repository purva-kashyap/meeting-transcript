"""
Authentication Service
Handles Microsoft authentication with delegated permissions
"""

import os
import msal
from flask import session, url_for


class AuthService:
    """Facade for Microsoft authentication using delegated permissions"""
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.client_id = os.getenv('MICROSOFT_CLIENT_ID', '')
        self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET', '')
        self.authority = os.getenv('MICROSOFT_AUTHORITY', 'https://login.microsoftonline.com/common')
        self.redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', 'http://localhost:5001/auth/callback')
        
        # Delegated permissions (user consent required)
        self.scopes = [
            "User.Read",
            "Calendars.Read",
            "OnlineMeetings.Read",
            "Chat.ReadWrite",
            "ChatMessage.Send"
        ]
        
        self.mock_user = {
            "id": "mock_user_123",
            "displayName": "Mock User",
            "mail": "user@example.com",
            "userPrincipalName": "user@example.com"
        }
    
    def _get_msal_app(self, cache=None):
        """
        Initialize and return MSAL ConfidentialClientApplication
        with token cache support
        """
        if not self.client_id or not self.client_secret:
            return None
        
        return msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
            token_cache=cache
        )
    
    def _build_auth_url(self, scopes=None, state=None):
        """
        Build the authorization URL for user login
        
        Args:
            scopes: List of permission scopes
            state: State parameter for CSRF protection
        
        Returns:
            Authorization URL string
        """
        if self.use_mock:
            # Return a mock URL that will be handled by our mock endpoint
            return url_for('auth_mock_login', _external=True)
        
        if scopes is None:
            scopes = self.scopes
        
        msal_app = self._get_msal_app()
        if not msal_app:
            raise Exception("Microsoft credentials not configured")
        
        auth_url = msal_app.get_authorization_request_url(
            scopes=scopes,
            state=state,
            redirect_uri=self.redirect_uri
        )
        
        return auth_url
    
    def get_login_url(self, state=None):
        """
        Get the Microsoft login URL
        
        Args:
            state: State parameter for CSRF protection
        
        Returns:
            Login URL string
        """
        return self._build_auth_url(state=state)
    
    def acquire_token_by_auth_code(self, auth_code, scopes=None, cache=None):
        """
        Exchange authorization code for access token
        
        Args:
            auth_code: Authorization code from callback
            scopes: List of permission scopes
            cache: Token cache instance
        
        Returns:
            Token response dictionary
        """
        if self.use_mock:
            # Return mock token
            return {
                "access_token": "mock_access_token_delegated",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "mock_refresh_token",
                "scope": " ".join(self.scopes),
                "id_token_claims": self.mock_user
            }
        
        if scopes is None:
            scopes = self.scopes
        
        msal_app = self._get_msal_app(cache=cache)
        if not msal_app:
            raise Exception("Microsoft credentials not configured")
        
        result = msal_app.acquire_token_by_authorization_code(
            code=auth_code,
            scopes=scopes,
            redirect_uri=self.redirect_uri
        )
        
        if "error" in result:
            raise Exception(f"Failed to acquire token: {result.get('error_description', result.get('error'))}")
        
        return result
    
    def acquire_token_silent(self, account, scopes=None, cache=None):
        """
        Acquire token silently using cached refresh token
        
        Args:
            account: User account object
            scopes: List of permission scopes
            cache: Token cache instance
        
        Returns:
            Token response dictionary or None
        """
        if self.use_mock:
            # Return mock token
            return {
                "access_token": "mock_access_token_delegated_refreshed",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": " ".join(self.scopes)
            }
        
        if scopes is None:
            scopes = self.scopes
        
        msal_app = self._get_msal_app(cache=cache)
        if not msal_app:
            return None
        
        result = msal_app.acquire_token_silent(
            scopes=scopes,
            account=account
        )
        
        return result
    
    def get_accounts(self, cache=None):
        """
        Get all cached accounts
        
        Args:
            cache: Token cache instance
        
        Returns:
            List of account dictionaries
        """
        if self.use_mock:
            return [self.mock_user]
        
        msal_app = self._get_msal_app(cache=cache)
        if not msal_app:
            return []
        
        return msal_app.get_accounts()
    
    def remove_account(self, account, cache=None):
        """
        Remove account from cache (logout)
        
        Args:
            account: User account object
            cache: Token cache instance
        """
        if self.use_mock:
            return
        
        msal_app = self._get_msal_app(cache=cache)
        if msal_app and account:
            msal_app.remove_account(account)
