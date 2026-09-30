import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parents[1]
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.auth import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_verifies_password():
    plain = "Admin@123"
    hashed = hash_password(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong-pass", hashed) is False


def test_access_token_contains_role_and_user():
    token = create_access_token("admin", "admin")
    payload = decode_access_token(token)

    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"
