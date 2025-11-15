#!/usr/bin/env python3
"""Download spaCy model wheel from GitHub releases for Docker caching."""

import json
import os
import sys
import urllib.request


def download_spacy_model(
    model_name="en_core_web_sm", output_dir=".local/cache/spacy-models"
):
    """Download spaCy model wheel from GitHub releases."""
    print(f"Fetching releases for {model_name}...")

    try:
        # Fetch releases from GitHub API (use per_page=100 to get more results)
        with urllib.request.urlopen(
            "https://api.github.com/repos/explosion/spacy-models/releases?per_page=100"
        ) as response:
            releases = json.loads(response.read().decode())
    except Exception as e:
        print(f"ERROR: Failed to fetch releases: {e}", file=sys.stderr)
        return False

    # Find the release for this model (releases are tagged by model name)
    model_release = None
    for release in releases:
        if model_name in release["tag_name"]:
            model_release = release
            break

    if not model_release:
        print(f"ERROR: Could not find release for {model_name}", file=sys.stderr)
        return False

    # Find the wheel file URL in the model's release assets
    whl_url = None
    for asset in model_release.get("assets", []):
        asset_name = asset["name"]
        if asset_name.endswith(".whl") and "py3-none-any" in asset_name:
            whl_url = asset["browser_download_url"]
            break

    if not whl_url:
        print(f"ERROR: Could not find {model_name} wheel in releases", file=sys.stderr)
        return False

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Download the wheel file
    output_path = os.path.join(output_dir, os.path.basename(whl_url))
    print(f"Downloading {whl_url}...")
    try:
        urllib.request.urlretrieve(whl_url, output_path)
        print(f"Model wheel downloaded successfully to {output_path}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to download wheel: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = download_spacy_model()
    sys.exit(0 if success else 1)
