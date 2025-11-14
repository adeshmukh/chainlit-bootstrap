"""Chainlit application entry point."""

# Import handlers to register them with Chainlit
# OAuth configuration happens automatically when auth module is imported
from chainlit_bootstrap import handlers  # noqa: F401
from chainlit_bootstrap.auth import oauth_callback  # noqa: F401
