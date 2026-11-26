import base64
import os
from dataclasses import asdict
from pathlib import Path
from time import time_ns
from typing import Any
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient
from pytest_mock import MockerFixture
from realerikrani.base64token import encode

from realerikrani.project import bearer_extractor, service_system
from realerikrani.project.app import register_project_with_trusted_system_endpoints
from realerikrani.project.blueprint import repo
from realerikrani.project.model import Project


@pytest.fixture
def client():
    os.environ["CREDENTIALS_DIRECTORY"] = str(
        Path(__file__).resolve().parents[2] / "test" / "demo_keys"
    )
    app = register_project_with_trusted_system_endpoints(Flask(__name__))
    app.testing = True
    return app.test_client()


@pytest.fixture
def system_auth(mocker: MockerFixture):
    mocker.patch.object(
        bearer_extractor,
        "get_bearer",
        return_value="system-token",
    )
    mocker.patch.object(service_system, "verify_jwt")


_GROUP_ID = uuid4()
PROJECT1 = Project("project1", uuid4(), time_ns())
PROJECT2 = Project("project2", uuid4(), time_ns())
PROJECT3 = Project("project3", uuid4(), time_ns())


def _project_dict(project: Project) -> dict:
    return asdict(project) | {"id": str(project.id)}


@pytest.mark.usefixtures("system_auth")
def test_it_reads_projects_empty_first_page(
    client: FlaskClient,
    mocker: MockerFixture,
):
    read_first_projects = mocker.patch.object(
        repo,
        "read_first_projects",
        return_value=[],
    )
    page_size = 1

    res = client.get(f"/system/projects?group_id={_GROUP_ID}&page_size={page_size}")

    assert res.status_code == 200
    assert res.json == {"projects": [], "next_page_token": None}
    read_first_projects.assert_called_once_with(_GROUP_ID, page_size + 1)


@pytest.mark.usefixtures("system_auth")
def test_it_reads_projects_filled_first_page(
    client: FlaskClient,
    mocker: MockerFixture,
):
    read_first_projects = mocker.patch.object(
        repo,
        "read_first_projects",
        return_value=[PROJECT1],
    )
    page_size = 1

    res = client.get(f"/system/projects?group_id={_GROUP_ID}&page_size={page_size}")

    assert res.status_code == 200
    assert res.json == {
        "projects": [_project_dict(PROJECT1)],
        "next_page_token": None,
    }
    read_first_projects.assert_called_once_with(_GROUP_ID, page_size + 1)


@pytest.mark.usefixtures("system_auth")
def test_it_reads_projects_overfilled_first_page(
    client: FlaskClient,
    mocker: MockerFixture,
):
    read_first_projects = mocker.patch.object(
        repo,
        "read_first_projects",
        return_value=[PROJECT3, PROJECT2, PROJECT1],
    )
    page_size = 2

    res = client.get(f"/system/projects?group_id={_GROUP_ID}&page_size={page_size}")

    assert res.status_code == 200
    assert res.json == {
        "projects": [
            _project_dict(PROJECT3),
            _project_dict(PROJECT2),
        ],
        "next_page_token": encode(
            [
                ("created_at_us", PROJECT2.created_at_us),
                ("id", str(PROJECT2.id)),
                ("page_size", page_size),
            ]
        ),
    }
    read_first_projects.assert_called_once_with(_GROUP_ID, page_size + 1)


@pytest.mark.usefixtures("system_auth")
def test_it_reads_projects_next_page(
    client: FlaskClient,
    mocker: MockerFixture,
):
    next_page_token = encode(
        [
            ("created_at_us", PROJECT1.created_at_us),
            ("id", str(PROJECT1.id)),
            ("page_size", 1),
        ]
    )
    read_next_projects = mocker.patch.object(
        repo,
        "read_next_projects",
        return_value=[],
    )

    res = client.get(
        f"/system/projects?group_id={_GROUP_ID}&page_token={next_page_token}"
    )

    assert res.status_code == 200
    assert res.json == {"projects": [], "next_page_token": None}
    read_next_projects.assert_called_once_with(
        _GROUP_ID,
        2,
        PROJECT1.created_at_us,
        PROJECT1.id,
    )


@pytest.mark.usefixtures("system_auth")
def test_it_reads_no_projects_for_no_params(client: FlaskClient):
    res = client.get(f"/system/projects?group_id={_GROUP_ID}")

    assert res.status_code == 400
    assert res.json == {
        "errors": [
            {
                "code": "PAGINATION_PARAMS_MISSING",
                "message": "page size or page token missing",
            }
        ]
    }


@pytest.mark.usefixtures("system_auth")
def test_it_reads_no_projects_for_non_int_page_size(client: FlaskClient):
    res = client.get(f"/system/projects?group_id={_GROUP_ID}&page_size=abc")

    assert res.status_code == 400
    assert res.json == {
        "errors": [
            {
                "code": "PAGINATION_PARAMS_MISSING",
                "message": "page size or page token missing",
            }
        ]
    }


@pytest.mark.usefixtures("system_auth")
def test_it_reads_no_projects_for_non_base64_page_token(client: FlaskClient):
    res = client.get(f"/system/projects?group_id={_GROUP_ID}&page_token=abc")

    assert res.status_code == 400
    assert res.json == {
        "errors": [
            {
                "code": "PAGINATION_PARAMS_MISSING",
                "message": "page size or page token missing",
            }
        ]
    }


@pytest.mark.usefixtures("system_auth")
def test_it_reads_no_projects_for_non_json_base64_decoded_page_token(
    client: FlaskClient,
):
    page_token = base64.urlsafe_b64encode(b"abc").decode()

    res = client.get(f"/system/projects?group_id={_GROUP_ID}&page_token={page_token}")

    assert res.status_code == 400
    assert res.json == {
        "errors": [
            {
                "code": "PAGINATION_PARAMS_MISSING",
                "message": "page size or page token missing",
            }
        ]
    }


@pytest.mark.usefixtures("system_auth")
@pytest.mark.parametrize(
    "content",
    [
        [("created_at_us", time_ns())],
        [("id", str(uuid4()))],
        [("id", str(uuid4())), ("page_size", "abc")],
    ],
)
def test_it_reads_no_projects_for_partial_page_token(
    client: FlaskClient,
    content: list[tuple[str, Any]],
):
    page_token = encode(content)

    res = client.get(f"/system/projects?group_id={_GROUP_ID}&page_token={page_token}")

    assert res.status_code == 400
    assert res.json == {
        "errors": [
            {
                "code": "PAGINATION_PARAMS_MISSING",
                "message": "page size or page token missing",
            }
        ]
    }
