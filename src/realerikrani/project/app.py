import os
from datetime import datetime
from pathlib import Path

from flask import Flask
from flask.json.provider import DefaultJSONProvider
from realerikrani.flaskapierr import handle_error
from werkzeug.routing import UUIDConverter

from realerikrani.project.blueprint import key_blueprint, project_blueprint
from realerikrani.project.blueprint_system import make_system_blueprint


def _load_system_key() -> str:
    credentials_dir = os.environ.get("CREDENTIALS_DIRECTORY")
    if not credentials_dir:
        raise RuntimeError("CREDENTIALS_DIRECTORY is not set or is empty")

    system_key_path = Path(credentials_dir) / "system-key"

    try:
        system_key = system_key_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        msg = f"Cannot read Flask secret key: {system_key_path}"
        raise RuntimeError(msg) from exc

    if not system_key:
        raise RuntimeError("System key is empty")

    return system_key


def _register_common(app: Flask) -> None:
    app.url_map.converters["uuid"] = UUIDConverter
    app.register_blueprint(project_blueprint, url_prefix="/projects")
    app.register_blueprint(key_blueprint, url_prefix="/keys")
    app.register_error_handler(Exception, handle_error)
    app.json = DefaultJSONProvider(app)
    app.json.default = lambda obj: (
        obj.isoformat()
        if isinstance(obj, datetime)
        else DefaultJSONProvider.default(obj)
    )


def register_project(app: Flask) -> Flask:
    _register_common(app)
    return app


def register_project_with_trusted_system_endpoints(app: Flask) -> Flask:
    _register_common(app)

    system_key = _load_system_key()
    bp_system = make_system_blueprint(system_key)
    app.register_blueprint(bp_system, url_prefix="/system")

    return app
