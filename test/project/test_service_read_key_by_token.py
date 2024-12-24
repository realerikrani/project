from datetime import UTC, datetime, timedelta
from typing import Final
from uuid import UUID, uuid4

import jwt
import pytest
from pytest_mock import MockerFixture

from realerikrani.project.error import (
    ProjectTokenError,
    ProjectTokenKeyIdInvalidError,
    ProjectTokenKeyIdNotFoundError,
    PublicKeyNotFoundError,
)
from realerikrani.project.model import PublicKey
from realerikrani.project.service import read_key_by_token, repo

_PEM_PRIVATE: Final[str] = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA9f2kRmP+UnSyC9IheTJ9/OBdWHdZOeBFKnbHZbH3wdPnLo0V
Fr0fpaB40jr5v76eiCKrK9eT63G515glc0HHtyoim8gh5C8Xh3zGcV+5tV2uDTEJ
nrxts9cXwOBWdonbT0/0gkZJaS4N3ixQgbwgdhAAqKHAiye2xMfNjbD1A3diuzn5
IClQv3DgTqlCcprDzziDFUeMe4R4IiHmD6AB/gTZ52SJoXjPiSsXSEbvkCXkZk5M
u1rGIgm5Lw1uzA3hKzRD75OsWLCygX++gX10oe0knZyIWP229YfBBDwpVU8+Qfvp
wc+48SEC9+phMjvtkdslXuLSlWPtqQTdp/ti8QIDAQABAoIBAHzrRn4cj21OJ5CL
MEZ81rARPDYNvbj/ZABxe0bwfpHmy1K/gIMgna6ddF3GZ0fxRE571JMaEdsR0L9k
WzhRolsowZR8qIFZTMiYG6o9Y3Bv11CJo4oBxG/8feqLwjzGOyHmx5NUoDkSkyZN
OMD5ST7LV5pLMh04mL8LfB5FS9dqzUQYrw4ll6ofHCriKZcHPu5YCxPg2tVbfct3
MrzBAbUN5/DuRIMcGNAaPApZkqUS4Qb2enWOGf/b+KImqOBXjKN1oGPcR3xLpDOY
iX3lbWwENIhOzNaZP7eJlH2kPlLAXfvYgpxnD5iSwojxkHPtoe4ySPNVQfwkaejV
xYzFb/ECgYEA/8IgqyeUliZqtmKFTxKBZkDo0dlqSBwouVYUpSLpihpM0SyZgFXU
Z54a83Pb0nK+1ff4JdWdItbnFGKPZPltH1cQRpNHvjrZYGEXxPVSHAY6mSITsXpE
FVZDQbGCe6y3hmY4QV5vCFhv9mSPjYEF7TTSfXWns84sjWoFiCFdX4UCgYEA9jkm
sgAFnI/45IhBm5GhL0yFaxE8QEVfPnhyV2DRpgiowfa8YSbG766MktZaIyneDVEe
PiCSuimPRHhQ0QJSwH90247MMV8lVnSVImGl7LNIwlqYMQyB+BM1PG5fZ4eqTeYB
nyKi0ZFICTtZVtyGPRISp4t2giA/wJJxiQ7/c30CgYEAn7q78Gi90bCYgOOy4hlq
m1P6k+S3DeYYQPfT2Pae6FNYmmLCU3ZHO5dwuY8oQJzNNpCxd9+bTcDtfLu5VpS4
ZBRZ49njupjCXgEFeUrFRx9UxYKUzgjQMIs5YfPczCSoUdXRWHID4jBpbHaNeRCV
hPmyZAxw+kjPZlpKriQ4TokCgYBzoxWsRVxdUjSHSALgCD4WE68ZQKf2W15G3ZR9
uwfbHXf8WF/SlL6bdHOqxqbgmtohkPZOIUgnzDrv4j26W4f3xiRgtSjrCw9jEi+0
TP37M5w5Qwj1CDXGB2daMU/3NHzkRuB+F2s2Vy/ovgnQRJN6/RDrxRDsPi8SxvQx
dWy9lQKBgEr65suLseniMmhIhrq+d2lbtL6kP2EplOQFAGyrhjlT7LDtLf1TB2dB
n3cdlnibuLShSIZr71yEws6rD/cYNZOUvmFwqZUfHjeD/SnvD791+aL0DlBtHVu4
jL/oRHmRus/wIQupq7/qNaSKrGEeLpMruj+/Jo5jX+IuySZzvf+Y
-----END RSA PRIVATE KEY-----
"""
_PEM_PUBLIC: Final[str] = """
-----BEGIN RSA PUBLIC KEY-----
MIIBCgKCAQEA9f2kRmP+UnSyC9IheTJ9/OBdWHdZOeBFKnbHZbH3wdPnLo0VFr0f
paB40jr5v76eiCKrK9eT63G515glc0HHtyoim8gh5C8Xh3zGcV+5tV2uDTEJnrxt
s9cXwOBWdonbT0/0gkZJaS4N3ixQgbwgdhAAqKHAiye2xMfNjbD1A3diuzn5IClQ
v3DgTqlCcprDzziDFUeMe4R4IiHmD6AB/gTZ52SJoXjPiSsXSEbvkCXkZk5Mu1rG
Igm5Lw1uzA3hKzRD75OsWLCygX++gX10oe0knZyIWP229YfBBDwpVU8+Qfvpwc+4
8SEC9+phMjvtkdslXuLSlWPtqQTdp/ti8QIDAQAB
-----END RSA PUBLIC KEY-----
"""
_KEY_ID: UUID = uuid4()
_PROJECT_ID = uuid4()
_PUBLIC_KEY = PublicKey(
    id=_KEY_ID,
    pem=_PEM_PUBLIC,
    project_id=_PROJECT_ID,
    created_at=datetime.now(tz=UTC) - timedelta(minutes=5),
)


@pytest.fixture
def kid_value() -> str:
    return str(_KEY_ID)


@pytest.fixture
def expiration_minutes() -> int:
    return 5


@pytest.fixture
def payload(expiration_minutes: int):
    return {
        "iss": str(_PROJECT_ID),
        "iat": datetime.now(tz=UTC),
        "exp": datetime.now(tz=UTC) + timedelta(minutes=expiration_minutes),
    }


@pytest.fixture
def token(payload: dict, kid_value: str):
    return jwt.encode(
        payload=payload,
        key=_PEM_PRIVATE,
        algorithm="RS256",
        headers={"kid": kid_value},
    )


def test_it_decodes_token(token: str, mocker: MockerFixture):
    # given
    read_key = mocker.patch.object(repo, "read_key", return_value=_PUBLIC_KEY)

    # when
    result = read_key_by_token(token)

    # then
    read_key.assert_called_once_with(_KEY_ID)
    assert result == _PUBLIC_KEY


def test_it_raises_error_for_missing_public_key(token: str, mocker: MockerFixture):
    # given
    mocker.patch.object(repo, "read_key", side_effect=PublicKeyNotFoundError)

    # then
    with pytest.raises(PublicKeyNotFoundError):
        # when
        read_key_by_token(token)


def test_it_raises_error_for_missing_public_key_id(payload: dict):
    # given
    token = jwt.encode(payload=payload, key=_PEM_PRIVATE, algorithm="RS256")

    # then
    with pytest.raises(ProjectTokenKeyIdNotFoundError):
        # when
        read_key_by_token(token)


@pytest.mark.parametrize("kid_value", ["not an uuid"])
def test_it_raises_error_for_invalid_public_key_id(token: str):
    # then
    with pytest.raises(ProjectTokenKeyIdInvalidError):
        # when
        read_key_by_token(token)


@pytest.mark.parametrize("expiration_minutes", [-5])
def test_it_raises_error_for_expired_token(token: str, mocker: MockerFixture):
    # given
    mocker.patch.object(repo, "read_key", return_value=_PUBLIC_KEY)

    # then
    with pytest.raises(ProjectTokenError):
        # when
        read_key_by_token(token)
