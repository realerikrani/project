import base64
from pathlib import Path
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from realerikrani.project import service
from realerikrani.project.error import PublicKeyInvalidError

_INVALID_KEY = f"""
-----BEGIN PUBLIC KEY-----
{base64.b64encode(b".")}
-----END PUBLIC KEY-----
"""


@pytest.fixture
def key():
    with Path.open(Path("test/demo_keys/public_key.pem")) as pk:
        return pk.read()


@pytest.fixture
def key_validation_spy(mocker: MockerFixture, key: str):
    valid_key = mocker.spy(service, "validate_public_key")
    yield
    valid_key.assert_called_once_with(key)


@pytest.mark.parametrize("key", ["", _INVALID_KEY])
def test_it_disallows_invalid_key(key: str):
    # then
    with pytest.raises(PublicKeyInvalidError):
        service.validate_public_key(key)


def test_it_creates_key(mocker: MockerFixture, key_validation_spy: None, key: str):
    # given
    create_key = mocker.patch.object(service.repo, "create_key")

    # when
    result = service.create_key(uuid4(), key)

    # then
    assert result == create_key.return_value


def test_it_creats_project_with_key(
    mocker: MockerFixture, key_validation_spy: None, key: str
):
    # given
    create_key = mocker.patch.object(service.repo, "create_project_with_key")

    # when
    result = service.create_project_with_key("name", key)

    # then
    assert result == create_key.return_value
