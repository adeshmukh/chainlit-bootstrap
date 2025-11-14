"""Google OAuth authentication configuration for Chainlit."""

import os
from typing import Dict, Optional

import chainlit as cl


def configure_google_oauth():
    """Configure Google OAuth environment variables from custom names to Chainlit's expected names."""
    # Map user-provided environment variables to Chainlit's expected names
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    oauth_redirect_uri = os.getenv("OAUTH_REDIRECT_URI")

    if google_client_id:
        os.environ["OAUTH_GOOGLE_CLIENT_ID"] = google_client_id
    if google_client_secret:
        os.environ["OAUTH_GOOGLE_CLIENT_SECRET"] = google_client_secret
    if oauth_redirect_uri:
        os.environ["OAUTH_REDIRECT_URI"] = oauth_redirect_uri


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    """
    OAuth callback handler for Google authentication.
    
    This function is called after a user successfully authenticates with Google.
    By default, it allows all authenticated Google users to access the app.
    
    Args:
        provider_id: The OAuth provider identifier (e.g., "google")
        token: The OAuth token received from the provider
        raw_user_data: User information returned by the provider
        default_user: A cl.User object created by Chainlit
        
    Returns:
        A cl.User object if authentication is successful, None otherwise
    """
    if provider_id == "google":
        # Allow all authenticated Google users
        # You can customize this to restrict access, e.g., by domain:
        # if raw_user_data.get("hd") == "example.org":
        #     return default_user
        return default_user
    return None

