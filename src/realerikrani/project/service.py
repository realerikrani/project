from datetime import datetime
from typing import Any, Final
from uuid import UUID

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from . import repo
from .error import (
    ProjectTokenError,
    ProjectTokenKeyIdInvalidError,
    ProjectTokenKeyIdNotFoundError,
    PublicKeyInvalidError,
)
from .model import Project, PublicKey

_ALGORITHM: Final[str] = "RS256"


def validate_public_key(pem_data: str) -> None:
    try:
        serialization.load_pem_public_key(pem_data.encode())
    except ValueError as e:
        raise PublicKeyInvalidError from e


def create_project_with_key(name: str, pem: str) -> tuple[Project, PublicKey]:
    """Creates new project with an associated public key.

    Args:
      name: A name for the project.
      pem: A PEM for the key.

    Returns:
      The new project.
      The new public key.

    Raises:
      ProjectNameError: If name is invalid.
      PublicKeyInvalidError: If PEM is invalid.
      PublicKeyDuplicateError: If PEM is already used.
    """
    validate_public_key(pem)
    return repo.create_project_with_key(name, pem)


def create_key(project_id: UUID, pem: str) -> PublicKey:
    validate_public_key(pem)
    return repo.create_key(project_id, pem)


def read_key_by_token(token: str) -> PublicKey:
    """Decodes token.

    Returns:
        Public key corresponding to the key id

    Raises:
        ProjectTokenKeyIdInvalidError: token had an invalid "kid"
        ProjectTokenError: token could not be decoded
        ProjectTokenKeyIdNotFoundError: token "kid" did not exist
        PublicKeyNotFoundError: token's key was not in the db
    """
    try:
        kid = jwt.get_unverified_header(token)["kid"]
    except KeyError:
        raise ProjectTokenKeyIdNotFoundError from None

    try:
        key = repo.read_key(UUID(kid))
    except ValueError:
        raise ProjectTokenKeyIdInvalidError from None

    public_key = serialization.load_pem_public_key(key.pem.encode())
    if not isinstance(public_key, rsa.RSAPublicKey):
        raise PublicKeyInvalidError

    try:
        jwt.decode(
            token, key=public_key, algorithms=[_ALGORITHM], issuer=str(key.project_id)
        )
    except jwt.InvalidTokenError:
        raise ProjectTokenError from None

    return key


def read_keys(
    project_id: UUID, page_size: int, data: list[tuple[str, Any]]
) -> tuple[list[PublicKey], list[tuple[str, Any]] | None]:
    if not data:
        keys = repo.read_first_keys(project_id, page_size + 1)
    else:
        created_at = datetime.fromisoformat(data[0][1])
        keys = repo.read_next_keys(project_id, page_size + 1, created_at)

    next_token = None
    if len(keys) == page_size + 1:
        keys = keys[:-1]
        next_token = [
            ("created_at", keys[-1].created_at.isoformat()),
            ("page_size", page_size),
        ]
    return keys, next_token
