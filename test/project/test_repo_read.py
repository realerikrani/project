import os
import sqlite3
from contextlib import closing
from uuid import uuid4

import pytest

from realerikrani.project.error import (
    ProjectNotFoundError,
    PublicKeyNotFoundError,
)
from realerikrani.project.repo import (
    add_project_to_group,
    create_key,
    create_project_with_key,
    read_first_keys,
    read_first_projects,
    read_key,
    read_next_keys,
    read_next_projects,
    read_project,
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
def test_it_reads_project():
    # given
    project, _ = create_project_with_key("name", "pem")

    # when
    result = read_project(project.id)

    # then
    assert result == project


def test_it_reads_missing_project():
    # given
    project_id = uuid4()

    # then
    with pytest.raises(ProjectNotFoundError):
        # when
        read_project(project_id)


@pytest.mark.usefixtures("_clean_db")
def test_it_reads_public_key():
    # given
    _, key = create_project_with_key("p name", "a pem")

    # when
    result = read_key(key.id)

    # then
    assert result == key


def test_it_reads_missing_public_key():
    # given
    key_id = uuid4()

    # then
    with pytest.raises(PublicKeyNotFoundError):
        # when
        read_key(key_id)


@pytest.mark.usefixtures("_clean_db")
def test_it_reads_first_public_keys_by_project():
    # given
    create_project_with_key("p name0", "pem0")
    project1, _ = create_project_with_key("p name1", "pem1")
    key2 = create_key(project1.id, "pem2")
    key3 = create_key(project1.id, "pem3")

    # when
    result = read_first_keys(project1.id, size=2)

    # then
    assert result == [key3, key2]


@pytest.mark.usefixtures("_clean_db")
def test_it_reads_next_public_keys_by_project():
    # given
    create_project_with_key("p name0", "pem0")
    project1, key1 = create_project_with_key("p name1", "pem1")
    key2 = create_key(project1.id, "pem2")
    key3 = create_key(project1.id, "pem3")

    # when
    result = read_next_keys(project1.id, 2, key3.created_at)

    # then
    assert result == [key2, key1]


@pytest.mark.usefixtures("_clean_db")
def test_it_reads_first_projects():
    # given
    group_id1 = uuid4()
    group_id2 = uuid4()
    project1, _ = create_project_with_key("p name1", "pem1")
    project2, _ = create_project_with_key("p name2", "pem2")
    project3, _ = create_project_with_key("p name3", "pem3")
    project4, _ = create_project_with_key("p name4", "pem4")
    project5, _ = create_project_with_key("p name5", "pem5")
    add_project_to_group(group_id1, project1.id)
    add_project_to_group(group_id1, project2.id)
    add_project_to_group(group_id1, project3.id)
    add_project_to_group(group_id2, project4.id)
    add_project_to_group(group_id2, project5.id)

    # when
    result_group1 = read_first_projects(group_id1, size=2)
    result_group2 = read_first_projects(group_id2, size=2)

    # then
    assert result_group1 == [project3, project2]
    assert result_group2 == [project5, project4]


@pytest.mark.usefixtures("_clean_db")
def test_it_reads_next_projects():
    # given
    group_id1 = uuid4()
    group_id2 = uuid4()
    project1, _ = create_project_with_key("p name1", "pem1")
    project2, _ = create_project_with_key("p name2", "pem2")
    project3, _ = create_project_with_key("p name3", "pem3")
    project4, _ = create_project_with_key("p name4", "pem4")
    project5, _ = create_project_with_key("p name5", "pem5")
    add_project_to_group(group_id1, project1.id)
    add_project_to_group(group_id1, project2.id)
    add_project_to_group(group_id1, project3.id)
    add_project_to_group(group_id2, project4.id)
    add_project_to_group(group_id2, project5.id)

    # when
    result_group1 = read_next_projects(
        group_id1, 2, project3.created_at_us, project3.id
    )
    result_group2 = read_next_projects(
        group_id2, 2, project3.created_at_us, project4.id
    )

    # then
    assert result_group1 == [project2, project1]
    assert result_group2 == []
