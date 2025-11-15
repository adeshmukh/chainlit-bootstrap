"""Chainlit application entry point."""

import logging
import re
from pathlib import Path

from chainlit_bootstrap.auth import is_no_login_mode


class SuppressReactDevtoolsFilter(logging.Filter):
    """Drop noisy react-devtools websocket messages from logs."""

    noisy_tokens = ("window_message", '"react-devtools')

    def filter(self, record):
        msg = record.getMessage()
        return not any(token in msg for token in self.noisy_tokens)


def configure_logging():
    """
    Configure logging to suppress DEBUG level messages, especially react-devtools noise.
    """
    # Set root logger to INFO level to suppress DEBUG messages
    logging.basicConfig(level=logging.INFO)

    spam_filter = SuppressReactDevtoolsFilter()
    logging.getLogger().addFilter(spam_filter)

    # Specifically suppress DEBUG logs from socketio/websocket libraries
    socketio_logger = logging.getLogger("socketio")
    socketio_logger.setLevel(logging.WARNING)
    socketio_logger.addFilter(spam_filter)

    engineio_logger = logging.getLogger("engineio")
    engineio_logger.setLevel(logging.WARNING)
    engineio_logger.addFilter(spam_filter)

    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


configure_logging()


def configure_auth_mode():
    """
    Configure authentication mode based on CHAINLIT_NO_LOGIN environment variable.
    
    If CHAINLIT_NO_LOGIN is set, modifies chainlit.toml to disable authentication
    before Chainlit loads the configuration.
    """
    if not is_no_login_mode():
        print("INFO: Authentication mode: ENABLED (Google OAuth)")
        return

    chainlit_toml_path = Path(__file__).parent / "chainlit.toml"
    if not chainlit_toml_path.exists():
        print(
            f"WARNING: chainlit.toml not found at {chainlit_toml_path}. "
            "Cannot disable authentication."
        )
        return

    content = chainlit_toml_path.read_text(encoding="utf-8")
    
    # Try regex pattern first (matches with comments)
    pattern = r"(\[features\.authentication\]\s*#.*?\n.*?# Enable authentication\s*\n)enabled\s*=\s*true"
    modified_content = re.sub(pattern, r"\1enabled = false", content, flags=re.MULTILINE)
    
    # Fallback: line-by-line parsing if regex didn't match
    if modified_content == content:
        lines = content.split("\n")
        in_auth_section = False
        modified_lines = []
        
        for line in lines:
            if line.strip().startswith("[features.authentication]"):
                in_auth_section = True
                modified_lines.append(line)
            elif in_auth_section and line.strip().startswith("enabled"):
                modified_lines.append(re.sub(r"enabled\s*=\s*true", "enabled = false", line))
                in_auth_section = False
            elif in_auth_section and line.strip().startswith("["):
                in_auth_section = False
                modified_lines.append(line)
            else:
                modified_lines.append(line)
        
        modified_content = "\n".join(modified_lines)
    
    chainlit_toml_path.write_text(modified_content, encoding="utf-8")
    print("INFO: No-login mode enabled. Authentication has been disabled in chainlit.toml")


configure_auth_mode()

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

_data_layer = None


def _initialize_database_tables(conninfo: str) -> None:
    """Initialize database tables synchronously before async operations."""
    try:
        from sqlalchemy import create_engine
        
        sync_conninfo = conninfo.replace("sqlite+aiosqlite:///", "sqlite:///")
        sync_engine = create_engine(sync_conninfo, echo=False)
        
        try:
            from chainlit.data.sql_alchemy import Base
            Base.metadata.create_all(sync_engine)
            print("INFO: Database tables initialized successfully")
        except ImportError:
            print("INFO: Database initialization will happen on first access")
        
        sync_engine.dispose()
    except Exception as e:
        print(f"INFO: Database initialization deferred: {type(e).__name__}")


@cl.data_layer
def get_data_layer():
    """Get or create the data layer instance."""
    global _data_layer
    
    if _data_layer is None:
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        db_path = data_dir / "chainlit.db"
        conninfo = f"sqlite+aiosqlite:///{db_path}"
        
        _data_layer = SQLAlchemyDataLayer(conninfo=conninfo)
        _initialize_database_tables(conninfo)
    
    return _data_layer




from chainlit_bootstrap import handlers  # noqa: F401
from chainlit_bootstrap.auth import oauth_callback  # noqa: F401
