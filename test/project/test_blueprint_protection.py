from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from realerikrani.project.app import register_project
from realerikrani.project.blueprint import bearer_extractor, service
from realerikrani.project.error import (
    ProjectError,
    ProjectTokenError,
    ProjectTokenKeyIdInvalidError,
    ProjectTokenKeyIdNotFoundError,
    PublicKeyNotFoundError,
)

if TYPE_CHECKING:
    from werkzeug.test import TestResponse


@pytest.fixture
def client():
    app = register_project(Flask(__name__))
    app.testing = True
    return app.test_client()


def test_it_requires_token(client: FlaskClient):
    assert {
        client.post("keys").status_code,
        client.delete(f"keys/{uuid4()}").status_code,
        client.get("projects").status_code,
        client.delete("projects").status_code,
    } == {HTTPStatus.UNAUTHORIZED}


@pytest.mark.parametrize(
    ("issue", "payload"),
    [
        (
            PublicKeyNotFoundError,
            {"code": "KEY_MISSING", "message": "Key not found for 'kid'"},
        ),
        (
            ProjectTokenKeyIdInvalidError,
            {"code": "KEY_ID_INVALID", "message": "Value of 'kid' is invalid"},
        ),
        (
            ProjectTokenKeyIdNotFoundError,
            {"code": "KEY_ID_MISSING", "message": "Auth token has no 'kid'"},
        ),
        (
            ProjectTokenError,
            {"code": "TOKEN_INVALID", "message": "Auth token decoding issue"},
        ),
    ],
)
def test_it_protects_reading_project_with_auth_issues(
    client: FlaskClient,
    mocker: MockerFixture,
    issue: ProjectError,
    payload: dict[str, str],
):
    # given
    mocker.patch.object(service, "read_key_by_token", side_effect=issue)
    mocker.patch.object(bearer_extractor, "get_bearer")

    # when
    results: list[TestResponse] = [
        client.post("keys"),
        client.delete(f"keys/{uuid4()}"),
        client.get("projects"),
        client.delete("projects"),
    ]

    # then
    for res in results:
        assert res.status_code == HTTPStatus.UNAUTHORIZED
        assert res.json == {"errors": [payload]}
