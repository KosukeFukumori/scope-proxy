import hashlib
import secrets


def generate_token() -> tuple[str, str]:
    """(生のトークン値, SHA-256ハッシュ) を返す。生の値はこの場でしか得られない。"""
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
