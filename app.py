"""Chainlit application entry point."""

import logging
import os
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
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level_name, None)
    if level is None or not isinstance(level, int):
        print(
            f"WARNING: Unknown LOG_LEVEL '{log_level_name}'. "
            "Defaulting to INFO."
        )
        level = logging.INFO

    logging.basicConfig(level=level, force=True)

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

# Ensure audio feature is enabled (workaround for config loading issue)
def ensure_audio_enabled():
    """Ensure audio feature is enabled programmatically."""
    try:
        import chainlit.config as cfg
        if hasattr(cfg.config, 'features') and hasattr(cfg.config.features, 'audio'):
            # Check current state
            current_enabled = cfg.config.features.audio.enabled
            print(f"INFO: Current audio enabled state: {current_enabled}")
            
            # Try to update using model_copy if it's a Pydantic model
            if hasattr(cfg.config.features.audio, 'model_copy'):
                updated_audio = cfg.config.features.audio.model_copy(update={'enabled': True})
                # Update the features object
                if hasattr(cfg.config.features, 'model_copy'):
                    updated_features = cfg.config.features.model_copy(update={'audio': updated_audio})
                    # This won't work if config is read-only, but let's try
                    cfg.config = cfg.config.model_copy(update={'features': updated_features})
                else:
                    cfg.config.features.audio = updated_audio
            else:
                # Direct assignment
                cfg.config.features.audio.enabled = True
            
            # Verify it's actually set
            final_state = cfg.config.features.audio.enabled
            if final_state:
                print("INFO: Audio feature successfully enabled programmatically")
            else:
                print(f"WARNING: Audio feature still disabled after attempt (current: {final_state})")
    except Exception as e:
        print(f"WARNING: Could not programmatically enable audio: {e}")
        import traceback
        traceback.print_exc()

# Call after chainlit import but before handlers
ensure_audio_enabled()
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.base import BaseStorageClient
from typing import Dict, Any, Union
import asyncio
from urllib.parse import quote

_data_layer = None


class LocalFileStorageClient(BaseStorageClient):
    """Local file-based storage client for blob storage."""

    def __init__(self, base_path: Path):
        """Initialize local file storage client.
        
        Args:
            base_path: Base directory path for storing files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        object_key: str,
        data: Union[bytes, str],
        mime: str = "application/octet-stream",
        overwrite: bool = True,
        content_disposition: str | None = None,
    ) -> Dict[str, Any]:
        """Upload a file to local storage."""
        file_path = self.base_path / object_key
        
        if isinstance(data, str):
            data_bytes = data.encode("utf-8")
        else:
            data_bytes = data
        
        def _write_file():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(data_bytes)
        
        await asyncio.to_thread(_write_file)
        
        return {
            "path": str(file_path),
            "size": len(data_bytes),
            "mime": mime,
        }

    async def delete_file(self, object_key: str) -> bool:
        """Delete a file from local storage."""
        file_path = self.base_path / object_key
        
        def _delete_file():
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        
        try:
            return await asyncio.to_thread(_delete_file)
        except Exception:
            return False

    async def get_read_url(self, object_key: str) -> str:
        """Get a URL to read the file (returns a file:// URL for local storage)."""
        file_path = self.base_path / object_key
        # Return a relative path that can be served by Chainlit
        return f"/files/{quote(object_key)}"

    async def close(self) -> None:
        """Close the storage client (no-op for local storage)."""
        pass


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

        # Configure blob storage for file uploads
        blob_storage_dir = Path(__file__).parent / ".local" / "data" / "blobs"
        blob_storage_client = LocalFileStorageClient(blob_storage_dir)

        _data_layer = SQLAlchemyDataLayer(
            conninfo=conninfo,
            storage_provider=blob_storage_client,
        )
        _initialize_database_tables(conninfo)

    return _data_layer




from chainlit_bootstrap import handlers  # noqa: F401
from chainlit_bootstrap.auth import oauth_callback  # noqa: F401

# Ensure audio is enabled after all imports (Chainlit may reload config)
ensure_audio_enabled()
