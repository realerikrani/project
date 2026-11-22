import os
import sqlite3
from datetime import UTC, datetime
from functools import partial
from time import time_ns
from uuid import UUID, uuid4

from realerikrani.sopenqlite import query

from .db import CREATE_TABLES
from .error import (
    ProjectNameError,
    ProjectNotFoundError,
    PublicKeyDuplicateError,
    PublicKeyNotFoundError,
)
from .model import Project, PublicKey

_query = partial(
    query,
    CREATE_TABLES,
    os.environ["PROJECT_DATABASE_PATH"],
    ["PRAGMA foreign_keys = 1"],
)


def to_project(row: sqlite3.Row | None) -> Project:
    if row is None:
        raise ProjectNotFoundError

    return Project(
        name=row["name"],
        id=UUID(row["id"]),
        created_at_us=row["created_at_us"],
    )


def to_public_key(row: sqlite3.Row | None) -> PublicKey:
    if row is None:
        raise PublicKeyNotFoundError
    return PublicKey(
        pem=row["pem"],
        created_at=datetime.fromtimestamp(row["created_at"], UTC),
        project_id=UUID(row["project_id"]),
        id=UUID(row["id"]),
    )


def read_project(id: UUID) -> Project:
    q = "SELECT * FROM project where id = ?"
    return to_project(_query(lambda c: c.execute(q, (str(id),)).fetchone()))


def delete_project(id: UUID) -> Project:
    q = "DELETE FROM project WHERE id = ? RETURNING *"
    return to_project(_query(lambda c: c.execute(q, (str(id),)).fetchone()))


def create_project_with_key(name: str, pem: str) -> tuple[Project, PublicKey]:
    qp = "INSERT INTO project(name, id, created_at_us) VALUES (?, ?, ?) RETURNING *"
    qk = """
    INSERT INTO public_key(project_id,created_at,pem,id) VALUES (?,?,?,?) RETURNING *
    """

    created_at_us = time_ns() // 1_000
    created_at = created_at_us / 1_000_000
    project_id = str(uuid4())
    key_id = str(uuid4())
    _qp = lambda c: c.execute(qp, (name, project_id, created_at_us)).fetchone()
    _qk = lambda c: c.execute(qk, (project_id, created_at, pem, key_id)).fetchone()

    try:
        project, key = _query(lambda c: (_qp(c), _qk(c)))
    except sqlite3.IntegrityError as err:
        if err.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK":
            reason = err.args[0].split(": ")[1]
            if 'length("name")' in reason:
                raise ProjectNameError from None
        elif err.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE" and err.args[
            0
        ].endswith("public_key.pem"):
            raise PublicKeyDuplicateError from None
        raise
    return to_project(project), to_public_key(key)


def read_first_projects(group_id: UUID, size: int) -> list[Project]:
    q = """
        SELECT p.* FROM project AS p
        JOIN group_project AS gp ON gp.project_id = p.id
        WHERE gp.group_id = ?
        ORDER BY created_at_us DESC, id DESC
        LIMIT ?
    """
    _q = lambda c: c.execute(q, (str(group_id), size)).fetchall()
    return [to_project(p) for p in _query(_q)]


def read_next_projects(
    group_id: UUID,
    size: int,
    last_created_at_us: int,
    last_id: UUID,
) -> list[Project]:
    q = """
        SELECT p.* FROM project AS p
        JOIN group_project AS gp ON gp.project_id = p.id
        WHERE gp.group_id = ? AND (created_at_us, id) < (?, ?)
        ORDER BY created_at_us DESC, id DESC
        LIMIT ?
    """
    _q = lambda c: c.execute(
        q, (str(group_id), last_created_at_us, str(last_id), size)
    ).fetchall()
    return [to_project(p) for p in _query(_q)]


def create_key(project_id: UUID, pem: str) -> PublicKey:
    q = """
    INSERT INTO public_key(project_id,created_at,pem,id) VALUES (?,?,?,?) RETURNING *
    """
    time = datetime.now(UTC).timestamp()
    id = str(uuid4())
    _q = lambda c: c.execute(q, (str(project_id), time, pem, id)).fetchone()

    try:
        return to_public_key(_query(_q))
    except sqlite3.IntegrityError as err:
        if err.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY":
            raise ProjectNotFoundError from None
        if err.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE" and err.args[0].endswith(
            "public_key.pem"
        ):
            raise PublicKeyDuplicateError from None
        raise


def read_key(id: UUID) -> PublicKey:
    q = "SELECT * FROM public_key where id = ?"
    return to_public_key(_query(lambda c: c.execute(q, (str(id),)).fetchone()))


def add_project_to_group(group_id: UUID, project_id: UUID) -> None:
    q = "INSERT INTO group_project(group_id, project_id)  VALUES (?,?)"
    _query(lambda c: c.execute(q, (str(group_id), str(project_id))))


def delete_project_from_group(group_id: UUID, project_id: UUID) -> None:
    q = "DELETE FROM group_project where group_id = ? AND project_id = ?"
    _query(lambda c: c.execute(q, (str(group_id), str(project_id))))


def read_first_keys(project_id: UUID, size: int) -> list[PublicKey]:
    q = "SELECT * FROM public_key WHERE project_id = ? ORDER BY created_at DESC LIMIT ?"
    _q = lambda c: c.execute(q, (str(project_id), size)).fetchall()
    return [to_public_key(k) for k in _query(_q)]


def read_next_keys(project_id: UUID, size: int, last_time: datetime) -> list[PublicKey]:
    q = """SELECT * FROM public_key
        WHERE project_id = ? AND created_at < ? ORDER BY created_at DESC LIMIT ?"""
    time = last_time.timestamp()
    _q = lambda c: c.execute(q, (str(project_id), time, size)).fetchall()
    return [to_public_key(k) for k in _query(_q)]


def delete_key(id: UUID, project_id: UUID) -> PublicKey:
    q = "DELETE FROM public_key WHERE id=? AND project_id=? RETURNING *"
    _q = _query(lambda c: c.execute(q, (str(id), str(project_id))).fetchone())
    return to_public_key(_q)
