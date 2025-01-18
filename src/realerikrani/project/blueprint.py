from uuid import UUID

from flask import Blueprint, request

from realerikrani.base64token import encode
from realerikrani.flaskapierr import Error, ErrorGroup
from realerikrani.project import bearer_extractor, payload_converter
from realerikrani.project.error import (
    ProjectNameError,
    ProjectNotFoundError,
    PublicKeyDuplicateError,
    PublicKeyInvalidError,
    PublicKeyNotFoundError,
)

from . import repo, service

project_blueprint = Blueprint("project", __name__)
key_blueprint = Blueprint("key", __name__)


def extract_public_key(req: dict) -> str:
    try:
        return str(req["public_key"])
    except KeyError:
        raise ErrorGroup(
            "400", [Error("public_key missing", "VALUE_MISSING")]
        ) from None


def to_name_key(req: dict) -> tuple[str, str]:
    errors = []

    try:
        name = req["name"]
    except KeyError:
        errors.append(Error("name missing", "VALUE_MISSING"))
    else:
        if not (1 <= len(name) <= 100):
            errors.append(Error("name length must be 1..100", "VALUE_INVALID"))
    try:
        public_key = extract_public_key(req)
    except* Error as e:
        errors.append(*e.exceptions)  # type: ignore[arg-type]

    if errors:
        raise ErrorGroup("400", errors)

    return name, public_key


@project_blueprint.route("", methods=["POST"])
def create_project_with_key():  # type: ignore[no-untyped-def]
    name, public_key = to_name_key(dict(request.json))  # type: ignore[arg-type]
    try:
        project, key = service.create_project_with_key(name, public_key)
    except (PublicKeyInvalidError, ProjectNameError) as bad_err:
        raise ErrorGroup("400", [Error(bad_err.message, bad_err.code)]) from None
    except PublicKeyDuplicateError as duplicate_err:
        raise ErrorGroup(
            "409", [Error(duplicate_err.message, duplicate_err.code)]
        ) from None
    return ({"project": project, "kid": key.id}, 201)


@key_blueprint.route("", methods=["POST"])
def create_new_key():  # type: ignore[no-untyped-def]
    current_key = bearer_extractor.protect()
    public_key = extract_public_key(dict(request.json))  # type: ignore[arg-type]
    try:
        key = service.create_key(current_key.project_id, public_key)
    except ProjectNotFoundError as pe:
        raise ErrorGroup("404", [Error(pe.message, pe.code)]) from None
    except PublicKeyInvalidError as e:
        raise ErrorGroup("400", [Error(e.message, e.code)]) from None

    return {"kid": key.id}, 201


@project_blueprint.route("", methods=["GET"])
def read_project():  # type: ignore[no-untyped-def]
    key = bearer_extractor.protect()
    try:
        return {"project": repo.read_project(key.project_id)}
    except ProjectNotFoundError as e:
        raise ErrorGroup("404", [Error(e.message, e.code)]) from None


@key_blueprint.route("", methods=["GET"])
def read_keys():  # type: ignore[no-untyped-def]
    key = bearer_extractor.protect()
    req_args = payload_converter.to_page_size_and_data(dict(request.args))
    if req_args is None:
        raise ErrorGroup(
            "400",
            [Error("page size or page token missing", "PAGINATION_PARAMS_MISSING")],
        ) from None

    page_size, data = req_args
    keys, token = service.read_keys(key.project_id, page_size, data)

    return {"keys": keys, "next_page_token": encode(token)}


@project_blueprint.route("", methods=["DELETE"])
def delete_project():  # type: ignore[no-untyped-def]
    key = bearer_extractor.protect()
    try:
        project = repo.delete_project(key.project_id)
    except ProjectNotFoundError as e:
        raise ErrorGroup("404", [Error(e.message, e.code)]) from None
    return {"project": project}


@key_blueprint.route("/<uuid:id>", methods=["DELETE"])
def delete_key(id: UUID):  # type: ignore[no-untyped-def]
    key_of_token = bearer_extractor.protect()
    try:
        key = repo.delete_key(id, key_of_token.project_id)
    except PublicKeyNotFoundError as e:
        raise ErrorGroup("404", [Error(e.message, e.code)]) from None
    return {"kid": key.id}
