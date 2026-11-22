from uuid import UUID

from flask import Blueprint, request
from realerikrani.base64token import encode
from realerikrani.flaskapierr import Error, ErrorGroup

from realerikrani.project import bearer_extractor, payload_converter

from . import repo, service, service_system


def make_system_blueprint(system_key: str) -> Blueprint:
    system_blueprint = Blueprint("system", __name__)

    @system_blueprint.route("/projects", methods=["GET"])
    def read_projects():  # type: ignore[no-untyped-def]  # noqa: ANN202
        group_id = UUID(request.args.get("group_id"))

        service_system.verify_jwt(bearer_extractor.get_bearer(), system_key)

        req_args = payload_converter.to_page_size_and_data(dict(request.args))
        if req_args is None:
            raise ErrorGroup(
                "400",
                [Error("page size or page token missing", "PAGINATION_PARAMS_MISSING")],
            ) from None

        page_size, data = req_args
        projects, token = service.read_projects(group_id, page_size, data)

        return {"projects": projects, "next_page_token": encode(token)}

    @system_blueprint.route(
        "/projects/<uuid:project_id>/groups/<uuid:group_id>", methods=["POST"]
    )
    def add_project_to_group(project_id: UUID, group_id: UUID):  # type: ignore[no-untyped-def]  # noqa: ANN202
        service_system.verify_jwt(bearer_extractor.get_bearer(), system_key)
        repo.add_project_to_group(group_id, project_id)
        return {}, 200

    @system_blueprint.route(
        "/projects/<uuid:project_id>/groups/<uuid:group_id>", methods=["DELETE"]
    )
    def delete_project_from_group(project_id: UUID, group_id: UUID):  # type: ignore[no-untyped-def]  # noqa: ANN202
        service_system.verify_jwt(bearer_extractor.get_bearer(), system_key)
        repo.delete_project_from_group(group_id, project_id)
        return {}, 200

    return system_blueprint
