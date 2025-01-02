from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Self
from uuid import UUID

import jwt
import pytest
import requests

DOMAIN = "http://127.0.0.1:8080"


@dataclass
class Key:
    key_id: UUID
    project_id: UUID
    private_key: str | None = None

    def to_token(self: Self):
        if self.private_key is None:
            pytest.fail("need a private key but it is None")
        return jwt.encode(
            payload={
                "iat": datetime.now(tz=UTC),
                "exp": datetime.now(tz=UTC) + timedelta(minutes=5),
                "iss": str(self.project_id),
            },
            key=self.private_key,
            algorithm="RS256",
            headers={"kid": str(self.key_id)},
        )


@dataclass
class KeyCtx:
    key: Key = field(init=False)
    auth: dict[str, str] = field(init=False)
    new_key: Key = field(init=False)
    new_auth: dict[str, str] = field(init=False)


@pytest.fixture(scope="module")
def ctx():
    return KeyCtx()


@pytest.mark.pysteptest
class TestProjects:
    def test_it_creates_project_with_key(self, ctx: KeyCtx):
        # given
        name = "any name"
        with Path.open(Path("test/demo_keys/private_key.pem")) as pp:
            private_key = pp.read()
        with Path.open(Path("test/demo_keys/public_key.pem")) as pk:
            public_key = pk.read()

        # when
        response = requests.post(
            f"{DOMAIN}/projects", json=dict(name=name, public_key=public_key)
        )
        r = response.json()

        # then
        assert response.status_code == requests.codes.created
        assert r["kid"]
        assert r["project"]
        ctx.key = Key(UUID(r["kid"]), r["project"]["id"], private_key)
        ctx.auth = {"Authorization": f"Bearer {ctx.key.to_token()}"}

    def test_it_reads_project(self, ctx: KeyCtx):
        # when
        result = requests.get(f"{DOMAIN}/projects", headers=ctx.auth)

        # then
        assert result.status_code == requests.codes.ok
        assert result.json()["project"]["id"] == ctx.key.project_id

    def test_it_deletes_project(self, ctx: KeyCtx):
        # when
        rd = requests.delete(f"{DOMAIN}/projects", headers=ctx.auth)

        # then
        assert rd.status_code == requests.codes.ok
        assert rd.json()["project"]["id"] == ctx.key.project_id
