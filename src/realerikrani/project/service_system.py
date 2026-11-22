from typing import Final

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from .error import (
    ProjectTokenError,
    PublicKeyInvalidError,
)

_ALGORITHM: Final[str] = "RS256"


def verify_jwt(token: str, public_key: str) -> None:
    key = serialization.load_pem_public_key(public_key.encode())
    if not isinstance(key, rsa.RSAPublicKey):
        raise PublicKeyInvalidError

    try:
        jwt.decode(token, key=key, algorithms=[_ALGORITHM], issuer="system")
    except jwt.InvalidTokenError:
        raise ProjectTokenError from None
