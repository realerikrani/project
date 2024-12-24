from dataclasses import asdict
from datetime import UTC, datetime
from http import HTTPStatus
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from realerikrani.project import bearer_extractor
from realerikrani.project.app import register_project
from realerikrani.project.blueprint import repo
from realerikrani.project.error import (
    ProjectNotFoundError,
    PublicKeyNotFoundError,
)
from realerikrani.project.model import Project, PublicKey

_PROJECT_ID = uuid4()
_KEY_ID = uuid4()


@pytest.fixture
def client():
    app = register_project(Flask(__name__))
    app.testing = True
    return app.test_client()


@pytest.fixture
def protect(mocker: MockerFixture):
    key = PublicKey(
        pem="any_pem",
        created_at=datetime.now(tz=UTC),
        project_id=_PROJECT_ID,
        id=_KEY_ID,
    )
    mocker.patch.object(bearer_extractor, "protect", return_value=key)


@pytest.mark.usefixtures("protect")
def test_it_deletes_project(client: FlaskClient, mocker: MockerFixture):
    # given
    project = Project("name", _PROJECT_ID)
    delete_project = mocker.patch.object(repo, "delete_project", return_value=project)

    # when
    res = client.delete("projects")

    # then
    assert res.status_code == HTTPStatus.OK
    assert res.json == {"project": asdict(project) | {"id": str(project.id)}}
    delete_project.assert_called_once_with(_PROJECT_ID)


@pytest.mark.usefixtures("protect")
def test_it_deletes_no_missing_project(client: FlaskClient, mocker: MockerFixture):
    # given
    error = ProjectNotFoundError()
    mocker.patch.object(repo, "delete_project", side_effect=error)

    # when
    res = client.delete("projects")

    # then
    assert res.status_code == HTTPStatus.NOT_FOUND
    assert res.json == {"errors": [{"code": error.code, "message": error.message}]}


@pytest.mark.usefixtures("protect")
def test_it_deletes_key(client: FlaskClient, mocker: MockerFixture):
    # given
    key = PublicKey("any_pem", datetime.now(tz=UTC), _PROJECT_ID, _KEY_ID)
    delete_key = mocker.patch.object(repo, "delete_key", return_value=key)

    # when
    res = client.delete(f"keys/{_KEY_ID}")

    # then
    assert res.status_code == HTTPStatus.OK
    assert res.json == {"kid": str(_KEY_ID)}
    delete_key.assert_called_once_with(_KEY_ID, _PROJECT_ID)


@pytest.mark.usefixtures("protect")
def test_it_deletes_no_missing_key(client: FlaskClient, mocker: MockerFixture):
    # given
    error = PublicKeyNotFoundError()
    mocker.patch.object(repo, "delete_key", side_effect=error)

    # when
    res = client.delete(f"keys/{uuid4()}")

    # then
    assert res.status_code == HTTPStatus.NOT_FOUND
    assert res.json == {"errors": [{"code": error.code, "message": error.message}]}
