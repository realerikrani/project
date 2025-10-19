import base64
from dataclasses import asdict
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient
from pytest_mock import MockerFixture
from realerikrani.base64token import encode

from realerikrani.project import bearer_extractor
from realerikrani.project.app import register_project
from realerikrani.project.blueprint import repo
from realerikrani.project.error import (
    ProjectNotFoundError,
)
from realerikrani.project.model import Project, PublicKey


def _p_dict(p: PublicKey) -> dict:
    return {
        "pem": p.pem,
        "created_at": p.created_at.isoformat(),
        "project_id": str(p.project_id),
        "id": str(p.id),
    }


_PROJECT_ID = uuid4()
PKEY1 = PublicKey(
    pem="any_pem",
    created_at=datetime.now(tz=UTC),
    project_id=_PROJECT_ID,
    id=uuid4(),
)
PKEY1_DICT = _p_dict(PKEY1)
PKEY2 = PublicKey(
    pem="any_pem2",
    created_at=datetime.now(tz=UTC),
    project_id=_PROJECT_ID,
    id=uuid4(),
)
PKEY2_DICT = _p_dict(PKEY2)
PKEY3 = PublicKey(
    pem="any_pem2",
    created_at=datetime.now(tz=UTC),
    project_id=_PROJECT_ID,
    id=uuid4(),
)
PKEY3_DICT = _p_dict(PKEY3)


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
        id=uuid4(),
    )
    mocker.patch.object(bearer_extractor, "protect", return_value=key)


@pytest.mark.usefixtures("protect")
def test_it_reads_project(client: FlaskClient, mocker: MockerFixture):
    # given
    project = Project("name", _PROJECT_ID)
    read_project = mocker.patch.object(repo, "read_project", return_value=project)

    # when
    res = client.get("projects")

    # then
    assert res.status_code == HTTPStatus.OK
    assert res.json == {"project": asdict(project) | {"id": str(project.id)}}
    read_project.assert_called_once_with(_PROJECT_ID)


@pytest.mark.usefixtures("protect")
def test_it_reads_no_missing_project(client: FlaskClient, mocker: MockerFixture):
    # given
    error = ProjectNotFoundError()
    mocker.patch.object(repo, "read_project", side_effect=error)

    # when
    res = client.get("projects")

    # then
    assert res.status_code == HTTPStatus.NOT_FOUND
    assert res.json == {"errors": [{"code": error.code, "message": error.message}]}


@pytest.mark.usefixtures("protect")
def test_it_reads_keys_empty_first_page(client: FlaskClient, mocker: MockerFixture):
    # given
    read_first_keys = mocker.patch.object(repo, "read_first_keys", return_value=[])
    page_size = 1

    # when
    res = client.get(f"keys?page_size={page_size}")

    # then
    assert res.status_code == HTTPStatus.OK
    assert res.json == {"keys": [], "next_page_token": None}
    read_first_keys.assert_called_once_with(_PROJECT_ID, page_size + 1)


@pytest.mark.usefixtures("protect")
def test_it_reads_keys_filled_first_page(client: FlaskClient, mocker: MockerFixture):
    # given
    read_first_keys = mocker.patch.object(repo, "read_first_keys", return_value=[PKEY1])
    page_size = 1

    # when
    res = client.get(f"keys?page_size={page_size}")

    # then
    assert res.status_code == HTTPStatus.OK
    assert res.json == {
        "keys": [PKEY1_DICT],
        "next_page_token": None,
    }
    read_first_keys.assert_called_once_with(_PROJECT_ID, page_size + 1)


@pytest.mark.usefixtures("protect")
def test_it_reads_keys_overfilled_first_page(
    client: FlaskClient, mocker: MockerFixture
):
    # given
    read_first_keys = mocker.patch.object(
        repo, "read_first_keys", return_value=[PKEY3, PKEY2, PKEY1]
    )
    page_size = 2

    # when
    res = client.get(f"keys?page_size={page_size}")

    # then
    assert res.status_code == HTTPStatus.OK
    assert res.json == {
        "keys": [PKEY3_DICT, PKEY2_DICT],
        "next_page_token": encode(
            [
                ("created_at", PKEY2.created_at.isoformat()),
                ("page_size", page_size),
            ]
        ),
    }
    read_first_keys.assert_called_once_with(_PROJECT_ID, page_size + 1)


@pytest.mark.usefixtures("protect")
def test_it_reads_keys_next_page(client: FlaskClient, mocker: MockerFixture):
    # given
    next_page_token = encode(
        [("created_at", PKEY1.created_at.isoformat()), ("page_size", 1)]
    )
    read_next_keys = mocker.patch.object(repo, "read_next_keys", return_value=[])
    page_size = 1

    # when
    res = client.get(f"keys?page_token={next_page_token}")

    # then
    assert res.status_code == HTTPStatus.OK
    assert res.json == {"keys": [], "next_page_token": None}
    read_next_keys.assert_called_once_with(_PROJECT_ID, page_size + 1, PKEY1.created_at)


@pytest.mark.usefixtures("protect")
def test_it_reads_no_keys_for_no_params(client: FlaskClient):
    # when
    res = client.get("keys")

    # then
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert res.json == {
        "errors": [
            {
                "code": "PAGINATION_PARAMS_MISSING",
                "message": "page size or page token missing",
            }
        ]
    }


@pytest.mark.usefixtures("protect")
def test_it_reads_no_keys_for_non_int_page_size(client: FlaskClient):
    # when
    res = client.get("keys?page_size=abc")

    # then
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert res.json == {
        "errors": [
            {
                "code": "PAGINATION_PARAMS_MISSING",
                "message": "page size or page token missing",
            }
        ]
    }


@pytest.mark.usefixtures("protect")
def test_it_reads_no_keys_for_non_base64_page_token(client: FlaskClient):
    # when
    res = client.get("keys?page_token=abc")

    # then
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert res.json == {
        "errors": [
            {
                "code": "PAGINATION_PARAMS_MISSING",
                "message": "page size or page token missing",
            }
        ]
    }


@pytest.mark.usefixtures("protect")
def test_it_reads_no_keys_for_non_json_base64_decoded_page_token(client: FlaskClient):
    # given
    next_page_token = base64.urlsafe_b64encode(b"abc").decode()

    # when
    res = client.get(f"keys?page_token={next_page_token}")

    # then
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert res.json == {
        "errors": [
            {
                "code": "PAGINATION_PARAMS_MISSING",
                "message": "page size or page token missing",
            }
        ]
    }


@pytest.mark.usefixtures("protect")
@pytest.mark.parametrize(
    "content",
    [
        [("created_at", datetime.now(tz=UTC).isoformat())],
        [("page_size", 1)],
        [("page_size", "abc")],
    ],
)
def test_it_reads_no_keys_for_partial_page_token(
    client: FlaskClient, content: list[tuple[str, Any]]
):
    # given
    next_page_token = encode(content)

    # when
    res = client.get(f"keys?page_token={next_page_token}")

    # then
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert res.json == {
        "errors": [
            {
                "code": "PAGINATION_PARAMS_MISSING",
                "message": "page size or page token missing",
            }
        ]
    }
