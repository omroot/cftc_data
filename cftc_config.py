from pathlib import Path


def load_cftc_credentials(filepath: Path) -> dict:
    """Parse the cftc_api_info file and return {'key_id': ..., 'key_secret': ...}."""
    credentials = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if key == 'CFTC_API_KEY_ID':
                credentials['key_id'] = value
            elif key == 'CFTC_API_KEY_SECRET':
                credentials['key_secret'] = value
    return credentials
