"""Google OAuth authentication configuration for Chainlit."""

import os
import secrets
from typing import Dict, Optional

import chainlit as cl


def configure_google_oauth():
    """
    Configure Google OAuth environment variables from custom names to Chainlit's expected names.
    
    Also ensures CHAINLIT_AUTH_SECRET is set, which is required for authentication to work.
    """
    # Map user-provided environment variables to Chainlit's expected names
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    oauth_redirect_uri = os.getenv("OAUTH_REDIRECT_URI")

    # Check if OAuth credentials are provided
    has_oauth_creds = bool(google_client_id and google_client_secret and oauth_redirect_uri)

    if google_client_id:
        os.environ["OAUTH_GOOGLE_CLIENT_ID"] = google_client_id
    if google_client_secret:
        os.environ["OAUTH_GOOGLE_CLIENT_SECRET"] = google_client_secret
    if oauth_redirect_uri:
        os.environ["OAUTH_REDIRECT_URI"] = oauth_redirect_uri

    # CHAINLIT_AUTH_SECRET is required for authentication to work
    # If not set, generate a random secret (for development only)
    # In production, this should be set explicitly via environment variable
    if not os.getenv("CHAINLIT_AUTH_SECRET"):
        # Generate a secure random secret
        auth_secret = secrets.token_urlsafe(32)
        os.environ["CHAINLIT_AUTH_SECRET"] = auth_secret
        if has_oauth_creds:
            print(
                "WARNING: CHAINLIT_AUTH_SECRET was not set. Generated a random secret. "
                "For production, set CHAINLIT_AUTH_SECRET explicitly."
            )

    # Warn if OAuth credentials are missing but authentication is enabled
    if not has_oauth_creds:
        print(
            "WARNING: Google OAuth credentials (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, "
            "OAUTH_REDIRECT_URI) are not set. Authentication will not be enforced. "
            "Set these environment variables to enable Google OAuth authentication."
        )


# Configure OAuth before the decorator is evaluated
configure_google_oauth()


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

