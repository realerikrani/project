import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pytest_mock import MockerFixture

from realerikrani.project import repo
from realerikrani.project.error import (
    ProjectNameError,
    ProjectNotFoundError,
    PublicKeyDuplicateError,
)
from realerikrani.project.repo import create_key, create_project_with_key


@pytest.fixture
def _clean_db():
    with closing(
        sqlite3.connect(os.environ["PROJECT_DATABASE_PATH"], uri=True, autocommit=True)
    ) as connection:
        yield
        connection.execute("PRAGMA foreign_keys = 1")
        connection.execute("DELETE FROM project")


@pytest.mark.usefixtures("_clean_db")
def test_it_creates_project_with_key():
    # given
    name = "project name"
    pem = "any pem-file content"
    current_date = datetime.now(UTC)

    # when
    result_project, result_key = create_project_with_key(name, pem)

    # then
    assert result_key.pem == pem
    assert result_project.name == name
    assert isinstance(result_project.id, UUID)
    assert result_project.id == result_key.project_id
    assert result_key.created_at.tzinfo == UTC
    assert result_key.created_at.date() == current_date.date()


@pytest.mark.parametrize("name", ["", "a" * 101])
def test_it_creates_no_project_with_invalid_name(name: str):
    # given
    pem = "any pem-file content"

    # then
    with pytest.raises(ProjectNameError):
        # when
        create_project_with_key(name, pem)


def test_it_creates_no_project_with_same_key():
    # given
    name = "project name"
    pem = "any pem-file content"
    create_project_with_key(name, pem)

    # then
    with pytest.raises(PublicKeyDuplicateError):
        # when
        create_project_with_key(name, pem)


def test_create_project_key_reraises_unknown_integrity_error(mocker: MockerFixture):
    # given
    mock_error = sqlite3.IntegrityError()
    mock_error.sqlite_errorname = "SQLITE_CONSTRAINT_UNKNOWN"
    mocker.patch.object(repo, "_query", side_effect=mock_error)

    # then
    with pytest.raises(sqlite3.IntegrityError):
        # when
        repo.create_project_with_key("any name", "any pem")


def test_create_project_key_reraises_unknown_constraint_error(mocker: MockerFixture):
    # given
    mock_error = sqlite3.IntegrityError()
    mock_error.sqlite_errorname = "SQLITE_CONSTRAINT_CHECK"
    mock_error.args = (": not expected",)
    mocker.patch.object(repo, "_query", side_effect=mock_error)

    # then
    with pytest.raises(sqlite3.IntegrityError):
        # when
        repo.create_project_with_key("any name", "any pem")


@pytest.mark.usefixtures("_clean_db")
def test_it_creates_key():
    # given
    pem = "any pem"
    current_date = datetime.now(UTC)
    project, _ = create_project_with_key("any name", "pem")

    # when
    result = create_key(project.id, pem)

    # then
    assert result.pem == pem
    assert result.project_id == project.id
    assert result.created_at.tzinfo == UTC
    assert result.created_at.date() == current_date.date()


def test_it_creates_no_key_for_missing_project():
    # given
    pem = "any_pem"

    # then
    with pytest.raises(ProjectNotFoundError):
        # when
        create_key(uuid4(), pem)


def test_it_creates_no_duplicate_key():
    # given
    pem = "any_pem"
    project, _ = create_project_with_key("any name", pem)

    # then
    with pytest.raises(PublicKeyDuplicateError):
        # when
        create_key(project.id, pem)


def test_create_key_reraises_unknown_integrity_error(mocker: MockerFixture):
    # given
    project_id = uuid4()
    pem = "any pem"
    mock_error = sqlite3.IntegrityError()
    mock_error.sqlite_errorname = "SQLITE_CONSTRAINT_UNKNOWN"
    mocker.patch.object(repo, "_query", side_effect=mock_error)

    # then
    with pytest.raises(sqlite3.IntegrityError):
        # when
        repo.create_key(project_id, pem)
