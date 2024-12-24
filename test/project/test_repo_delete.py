import os
import sqlite3
from contextlib import closing
from uuid import uuid4

import pytest

from realerikrani.project.error import PublicKeyNotFoundError
from realerikrani.project.repo import (
    create_project_with_key,
    delete_key,
    delete_project,
)


@pytest.fixture
def _clean_db():
    with closing(
        sqlite3.connect(os.environ["PROJECT_DATABASE_PATH"], uri=True, autocommit=True)
    ) as connection:
        yield
        connection.execute("PRAGMA foreign_keys = 1")
        connection.execute("DELETE FROM project")


@pytest.mark.usefixtures("_clean_db")
def test_it_deletes_project():
    # given
    project, _ = create_project_with_key("name", "pem")

    # when
    result = delete_project(project.id)

    # then
    assert result == project


@pytest.mark.usefixtures("_clean_db")
def test_it_deletes_key():
    # given
    project, key = create_project_with_key("any project", "any pem")

    # when
    result = delete_key(key.id, project.id)

    # then
    assert result == key


@pytest.mark.usefixtures("_clean_db")
def test_it_deletes_no_missing_key():
    # given
    project, key = create_project_with_key("any project", "any pem")
    project2, key2 = create_project_with_key("any project", "any pem2")

    # then
    with pytest.raises(PublicKeyNotFoundError):
        # when
        delete_key(uuid4(), uuid4())

    # then
    with pytest.raises(PublicKeyNotFoundError):
        # when
        delete_key(key2.id, project.id)

    # then
    with pytest.raises(PublicKeyNotFoundError):
        # when
        delete_key(key.id, project2.id)
