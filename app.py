"""Chainlit application entry point."""

# Import handlers to register them with Chainlit
# OAuth configuration happens automatically when auth module is imported
from learn_chainlit import handlers  # noqa: F401
from learn_chainlit.auth import oauth_callback  # noqa: F401
