import logging
from typing import TYPE_CHECKING

from flask import request

from realerikrani.flaskapierr import Error, ErrorGroup
from realerikrani.project import service as project_service
from realerikrani.project.error import (
    ProjectTokenError,
    ProjectTokenKeyIdInvalidError,
    ProjectTokenKeyIdNotFoundError,
    PublicKeyNotFoundError,
)

if TYPE_CHECKING:
    from realerikrani.project.model import PublicKey

LOG = logging.getLogger(__package__)


def get_bearer() -> str:
    try:
        authorization_header = request.headers["Authorization"]
    except KeyError:
        raise ErrorGroup(
            "401", [Error(message="Header is missing", code="AUTH_HEADER_MISSING")]
        ) from None

    try:
        auth_scheme, bearer_token = authorization_header.split()
    except ValueError:
        raise ErrorGroup(
            "401", [Error(message="Header is invalid", code="AUTH_HEADER_INVALID")]
        ) from None

    errors: list[Error] = []
    if auth_scheme.lower() != "bearer":
        errors.append(
            Error(message="Header is missing bearer keyword", code="BEARER_MISSING")
        )

    try:
        _header, _payload, _signature = bearer_token.split(".")
    except ValueError:
        errors.append(
            Error(message="Header is missing bearer value", code="BEARER_MISSING")
        )

    if errors:
        raise ErrorGroup("401", errors)

    return bearer_token


def protect() -> "PublicKey":
    try:
        return project_service.read_key_by_token(get_bearer())
    except ProjectTokenKeyIdInvalidError:
        raise ErrorGroup(
            "401", [Error("Value of 'kid' is invalid", "KEY_ID_INVALID")]
        ) from None
    except PublicKeyNotFoundError:
        raise ErrorGroup(
            "401", [Error("Key not found for 'kid'", "KEY_MISSING")]
        ) from None
    except ProjectTokenKeyIdNotFoundError:
        raise ErrorGroup(
            "401", [Error("Auth token has no 'kid'", "KEY_ID_MISSING")]
        ) from None
    except ProjectTokenError:
        raise ErrorGroup(
            "401", [Error("Auth token decoding issue", "TOKEN_INVALID")]
        ) from None
