from datetime import datetime

from flask import Flask
from flask.json.provider import DefaultJSONProvider
from werkzeug.routing import UUIDConverter

from realerikrani.flaskapierr import handle_error
from realerikrani.project.blueprint import key_blueprint, project_blueprint


def register_project(app: Flask) -> Flask:
    app.url_map.converters["uuid"] = UUIDConverter
    app.register_blueprint(project_blueprint, url_prefix="/projects")
    app.register_blueprint(key_blueprint, url_prefix="/keys")
    app.register_error_handler(Exception, handle_error)
    app.json = DefaultJSONProvider(app)
    app.json.default = (
        lambda obj: obj.isoformat()
        if isinstance(obj, datetime)
        else DefaultJSONProvider.default(obj)
    )
    return app
