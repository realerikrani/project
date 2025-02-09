import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Self
from uuid import UUID

import jwt
import pytest
import requests

DOMAIN = os.getenv("DOMAIN", "http://127.0.0.1:8080")


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


@pytest.fixture(scope="module")
def key_ctx():
    with Path.open(Path("test/demo_keys/private_key6.pem")) as pk:
        private_key = pk.read()
    with Path.open(Path("test/demo_keys/public_key6.pem")) as pk:
        public_key = pk.read()

    resp = requests.post(
        f"{DOMAIN}/projects", json=dict(name="key_ctx", public_key=public_key)
    ).json()
    key = Key(
        UUID(resp["kid"]),
        project_id=UUID(resp["project"]["id"]),
        private_key=private_key,
    )
    result = KeyCtx()
    result.key = key
    result.auth = {"Authorization": f"Bearer {key.to_token()}"}

    return result


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


@pytest.mark.pysteptest
class TestKeys:
    @pytest.fixture(autouse=True, scope="class")
    def after_class(self, key_ctx: KeyCtx):
        yield
        requests.delete(f"{DOMAIN}/projects", headers=key_ctx.auth)

    def test_it_creates_key(self, key_ctx: KeyCtx):
        # given
        with Path.open(Path("test/demo_keys/private_key2.pem")) as pp:
            new_private_key = pp.read()
        with Path.open(Path("test/demo_keys/public_key2.pem")) as pk:
            new_key = pk.read()
        payload = {"public_key": new_key}

        # when
        result = requests.post(f"{DOMAIN}/keys", headers=key_ctx.auth, json=payload)
        r = result.json()

        # then
        assert result.status_code == requests.codes.created
        assert set(result.json().keys()) == {"kid"}
        k = Key(UUID(r["kid"]), key_ctx.key.project_id, new_private_key)
        key_ctx.new_key = k
        key_ctx.new_auth = {"Authorization": f"Bearer {k.to_token()}"}

    def test_it_uses_created_key_to_read_project(self, key_ctx: KeyCtx):
        # when
        result = requests.get(f"{DOMAIN}/projects", headers=key_ctx.new_auth)

        # then
        assert result.status_code == requests.codes.ok

    def test_it_deletes_key(self, key_ctx: KeyCtx):
        # given
        kid = key_ctx.new_key.key_id

        # when
        result = requests.delete(f"{DOMAIN}/keys/{kid}", headers=key_ctx.auth)

        # then
        assert result.status_code == requests.codes.ok
        assert result.json()["kid"] == str(kid)

    def test_it_reads_keys(self, key_ctx: KeyCtx):
        # given
        key = key_ctx.key
        headers = key_ctx.auth
        with (
            Path.open(Path("test/demo_keys/public_key3.pem")) as pk1,
            Path.open(Path("test/demo_keys/public_key4.pem")) as pk2,
            Path.open(Path("test/demo_keys/public_key5.pem")) as pk3,
        ):
            d = f"{DOMAIN}/keys"
            k1 = requests.post(d, headers=key_ctx.auth, json={"public_key": pk1.read()})
            k2 = requests.post(d, headers=key_ctx.auth, json={"public_key": pk2.read()})
            k3 = requests.post(d, headers=key_ctx.auth, json={"public_key": pk3.read()})

        # when
        result_1 = requests.get(f"{DOMAIN}/keys?page_size=2", headers=headers)
        result_2 = requests.get(
            f"{DOMAIN}/keys?page_token={result_1.json()['next_page_token']}",
            headers=headers,
        )

        # then
        assert result_1.status_code == requests.codes.ok
        assert result_1.json()["keys"][0]["id"] == k3.json()["kid"]
        assert set(result_1.json()["keys"][0].keys()) == {
            "created_at",
            "id",
            "pem",
            "project_id",
        }
        assert result_1.json()["keys"][1]["id"] == k2.json()["kid"]
        assert result_2.status_code == requests.codes.ok
        assert [k["id"] for k in result_2.json()["keys"]] == [
            k1.json()["kid"],
            str(key.key_id),
        ]
        assert result_2.json()["next_page_token"] is None
