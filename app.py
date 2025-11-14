"""Chainlit application entry point."""

import os
import re
from pathlib import Path


def configure_auth_mode():
    """
    Configure authentication mode based on CHAINLIT_NO_LOGIN environment variable.
    
    If CHAINLIT_NO_LOGIN is set, modifies chainlit.toml to disable authentication
    before Chainlit loads the configuration.
    """
    no_login = os.getenv("CHAINLIT_NO_LOGIN", "").strip().lower()
    if no_login and no_login not in ("0", "false", "no", ""):
        # No-login mode enabled - disable authentication in chainlit.toml
        chainlit_toml_path = Path(__file__).parent / "chainlit.toml"
        
        if chainlit_toml_path.exists():
            # Read the TOML file
            content = chainlit_toml_path.read_text(encoding="utf-8")
            
            # Modify the authentication enabled setting
            # Match: enabled = true (with optional whitespace)
            pattern = r"(\[features\.authentication\]\s*#.*?\n.*?# Enable authentication\s*\n)enabled\s*=\s*true"
            replacement = r"\1enabled = false"
            
            modified_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
            # If the pattern didn't match (maybe comments are different), try a simpler pattern
            if modified_content == content:
                # Try matching just the enabled line within the [features.authentication] section
                lines = content.split("\n")
                in_auth_section = False
                modified_lines = []
                
                for i, line in enumerate(lines):
                    if line.strip().startswith("[features.authentication]"):
                        in_auth_section = True
                        modified_lines.append(line)
                    elif in_auth_section and line.strip().startswith("enabled"):
                        # Replace enabled = true with enabled = false
                        modified_lines.append(re.sub(r"enabled\s*=\s*true", "enabled = false", line))
                        in_auth_section = False  # Reset after finding enabled
                    elif in_auth_section and line.strip().startswith("["):
                        # We've moved to a new section
                        in_auth_section = False
                        modified_lines.append(line)
                    else:
                        modified_lines.append(line)
                
                modified_content = "\n".join(modified_lines)
            
            # Write the modified content back
            chainlit_toml_path.write_text(modified_content, encoding="utf-8")
            print("INFO: No-login mode enabled. Authentication has been disabled in chainlit.toml")
        else:
            print(
                f"WARNING: chainlit.toml not found at {chainlit_toml_path}. "
                "Cannot disable authentication."
            )
    else:
        print("INFO: Authentication mode: ENABLED (Google OAuth)")


# Configure auth mode before importing Chainlit modules
configure_auth_mode()

# Import handlers to register them with Chainlit
# OAuth configuration happens automatically when auth module is imported
from chainlit_bootstrap import handlers  # noqa: F401
from chainlit_bootstrap.auth import oauth_callback  # noqa: F401
