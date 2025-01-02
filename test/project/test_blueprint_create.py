from datetime import UTC, datetime
from http import HTTPStatus
from unittest.mock import Mock
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from realerikrani.project import bearer_extractor
from realerikrani.project.app import register_project
from realerikrani.project.blueprint import repo, service
from realerikrani.project.error import ProjectNotFoundError, PublicKeyInvalidError
from realerikrani.project.model import Project, PublicKey

_KEY = Mock(
    autospec=PublicKey,
    pem="""-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAL3oW37IOnnXxKZ9GJ0Lk9m4s0HKg6fM
mrkE1DdS4ZwBo5UV2+V2ftq4m1Z0uLLA9h8+ERHXWXenTDbm0LhG/xkCAwEAAQ==
-----END PUBLIC KEY-----
""",
)


@pytest.fixture
def client():
    app = register_project(Flask(__name__))
    app.testing = True
    return app.test_client()


@pytest.fixture
def protect(mocker: MockerFixture):
    mocker.patch.object(bearer_extractor, "protect", return_value=_KEY)


@pytest.mark.usefixtures("protect")
def test_it_creates_project_and_key_forbids_invalid_key(
    client: FlaskClient, mocker: MockerFixture
):
    # given
    req = {"name": "any name", "public_key": _KEY.pem}
    error = PublicKeyInvalidError()
    mocker.patch.object(repo, "create_project_with_key", side_effect=error)

    # when
    res = client.post("projects", json=req)

    # then
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert res.json == {"errors": [{"code": error.code, "message": error.message}]}


@pytest.mark.usefixtures("protect")
def test_it_creates_project_and_key(client: FlaskClient, mocker: MockerFixture):
    # given
    name = "project1"
    req = {"name": name, "public_key": _KEY.pem}
    created_project = Project(name, uuid4())
    created_key = PublicKey("any pem", datetime.now(UTC), created_project.id, uuid4())
    create_project_with_key = mocker.patch.object(
        repo, "create_project_with_key", return_value=(created_project, created_key)
    )

    # when
    res = client.post("projects", json=req)

    # then
    assert res.status_code == HTTPStatus.CREATED
    assert res.json
    assert set(res.json.keys()) == {"project", "kid"}
    assert set(res.json["project"].keys()) == {"id", "name"}
    assert res.json["project"]["id"]
    assert res.json["project"]["name"] == name
    assert res.json["kid"] == str(created_key.id)
    create_project_with_key.assert_called_once_with(name, req["public_key"])


@pytest.mark.usefixtures("protect")
def test_it_requires_name(client: FlaskClient):
    # given
    req = {"any": "thing"}

    # when
    res = client.post("projects", json=req)

    # then
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert res.json == {
        "errors": [
            {"code": "VALUE_MISSING", "message": "name missing"},
            {"code": "VALUE_MISSING", "message": "public_key missing"},
        ]
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "public_key": ""},
        {"name": "i" * 101, "public_key": "any_key"},
    ],
)
def test_it_requires_name_validity(client: FlaskClient, payload: str):
    # when
    res = client.post("projects", json=payload)

    # then
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert res.json == {
        "errors": [
            {"code": "VALUE_INVALID", "message": "name length must be 1..100"},
        ]
    }


@pytest.mark.usefixtures("protect")
def test_it_creates_new_key(client: FlaskClient, mocker: MockerFixture):
    # given
    project_id = uuid4()
    req = {"public_key": _KEY.pem}
    created_key = PublicKey("any pem", datetime.now(UTC), project_id, uuid4())
    create_key = mocker.patch.object(repo, "create_key", return_value=created_key)

    # when
    res = client.post("keys", json=req)

    # then
    assert res.status_code == HTTPStatus.CREATED
    assert res.json
    assert set(res.json.keys()) == {"kid"}
    assert res.json["kid"] == str(created_key.id)
    create_key.assert_called_once_with(_KEY.project_id, req["public_key"])


@pytest.mark.usefixtures("protect")
def test_it_creates_no_new_key_for_missing_project(
    client: FlaskClient, mocker: MockerFixture
):
    # given
    error = ProjectNotFoundError()
    mocker.patch.object(repo, "create_key", side_effect=error)

    # when
    res = client.post("keys", json={"public_key": _KEY.pem})

    # then
    assert res.status_code == HTTPStatus.NOT_FOUND
    assert res.json == {"errors": [{"code": error.code, "message": error.message}]}


@pytest.mark.usefixtures("protect")
def test_it_creates_no_new_key_for_invalid_key(
    client: FlaskClient, mocker: MockerFixture
):
    # given
    error = PublicKeyInvalidError()
    mocker.patch.object(service, "create_key", side_effect=error)

    # when
    res = client.post("keys", json={"public_key": "a key"})

    # then
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert res.json == {
        "errors": [
            {
                "code": error.code,
                "message": error.message,
            },
        ]
    }
