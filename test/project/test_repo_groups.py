import os
import sqlite3
from contextlib import closing
from uuid import uuid4

import pytest

from realerikrani.project.repo import (
    add_project_to_group,
    create_project_with_key,
    delete_project_from_group,
    read_first_projects,
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
def test_it_adds_project_to_group():
    # given
    name = "project name"
    pem = "any pem-file content"
    project, _ = create_project_with_key(name, pem)
    group_id = uuid4()

    # when
    add_project_to_group(group_id, project.id)
    projects = read_first_projects(group_id, 2)
    projects_from_random_group = read_first_projects(uuid4(), 2)

    # then
    assert len(projects) == 1
    assert projects[0].id == project.id
    assert len(projects_from_random_group) == 0


@pytest.mark.usefixtures("_clean_db")
def test_it_deletes_project_from_group():
    # given
    name = "project name"
    pem = "any pem-file content"
    project, _ = create_project_with_key(name, pem)
    group_id = uuid4()

    # when
    add_project_to_group(group_id, project.id)
    delete_project_from_group(group_id, project.id)
    projects = read_first_projects(group_id, 2)

    # then
    assert len(projects) == 0
