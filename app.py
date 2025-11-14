"""Chainlit application entry point."""

# Configure Google OAuth before importing handlers
from learn_chainlit.auth import configure_google_oauth

configure_google_oauth()

# Import handlers to register them with Chainlit
from learn_chainlit import handlers  # noqa: F401
from learn_chainlit.auth import oauth_callback  # noqa: F401
